from __future__ import annotations

import random
import time
import asyncio
import json
import logging
import threading
import time as timelib
from datetime import datetime, timezone
from typing import Any

from providers.provider_base import ProviderBase
from models.market_event import MarketEvent


class OKXProvider(ProviderBase):
    """
    OKX depth/trade provider; falls back to mock feed if websockets unavailable.
    """

    def __init__(self, event_bus, settings, symbol) -> None:
        super().__init__(event_bus, settings, symbol)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ws_tasks = []
        self._failures = 0
        self._backoff = 1.0
        self._last_msg = timelib.time()
        self._running = False

    def start(self) -> None:
        try:
            import websockets  # type: ignore

            self._loop = asyncio.new_event_loop()
            t = threading.Thread(target=self._run_ws, daemon=True)
            t.start()
            self._thread = t
        except Exception as exc:
            logging.getLogger(__name__).warning("OKX websockets unavailable (%s); falling back to mock feed", exc)
            self._start_thread(self._run_mock)

    def stop(self) -> None:
        self._running = False
        if self._loop:
            for task in self._ws_tasks:
                task.cancel()
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._stop_thread()

    def subscribe_dom(self) -> None:
        return

    def subscribe_trades(self) -> None:
        return

    def subscribe_quotes(self) -> None:
        return

    async def _ws_consume(self, url: str, msg: dict) -> None:
        import websockets  # type: ignore

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    await ws.send(json.dumps(msg))
                    async for raw in ws:
                        try:
                            data = json.loads(raw)
                        except Exception:
                            continue
                        self._last_msg = timelib.time()
                        self._backoff = 1.0
                        arg = data.get("arg", {})
                        channel = arg.get("channel")
                        if channel == "books5" or channel == "books50-l2-tbt":
                            self._handle_depth(data)
                        elif channel == "trades":
                            self._handle_trade(data)
            except Exception as exc:
                self._failures += 1
                logging.getLogger(__name__).warning("OKX WS reconnecting after error: %s (fail=%s)", exc, self._failures)
                if self._failures >= 3:
                    logging.getLogger(__name__).error("OKX WS failed 3 times; falling back to mock feed")
                    self._start_thread(self._run_mock)
                    return
                await asyncio.sleep(min(10.0, self._backoff))
                self._backoff = min(10.0, self._backoff * 2)

    def _run_ws(self) -> None:
        if not self._loop:
            return
        asyncio.set_event_loop(self._loop)
        self._running = True
        stream = self.symbol.upper()
        depth_msg = {"op": "subscribe", "args": [{"channel": "books5", "instId": stream}]}
        trade_msg = {"op": "subscribe", "args": [{"channel": "trades", "instId": stream}]}
        depth_url = "wss://ws.okx.com:8443/ws/v5/public"
        self._ws_tasks = [
            self._loop.create_task(self._ws_consume(depth_url, depth_msg)),
            self._loop.create_task(self._ws_consume(depth_url, trade_msg)),
            self._loop.create_task(self._heartbeat_watch()),
        ]
        self._loop.run_forever()

    async def _heartbeat_watch(self) -> None:
        while self._running:
            await asyncio.sleep(5.0)
            if timelib.time() - self._last_msg > 10.0:
                logging.getLogger(__name__).warning("OKX WS stale; reconnecting")
                self._failures += 1
                self._backoff = min(10.0, self._backoff * 2)
                self._running = False
                self._loop.call_soon_threadsafe(self._loop.stop)
                return

    def _handle_depth(self, data: dict) -> None:
        books = data.get("data", [])
        if not books:
            return
        book = books[0]
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        dom = []
        for price, size, *_ in bids:
            dom.append({"price": float(price), "bid_size": float(size), "ask_size": 0.0})
        for price, size, *_ in asks:
            dom.append({"price": float(price), "bid_size": 0.0, "ask_size": float(size)})
        evt = self.normalize_dom({"dom": dom})
        self.bus.publish(evt)

    def _handle_trade(self, data: dict) -> None:
        trades = data.get("data", [])
        if not trades:
            return
        tr = trades[0]
        price = float(tr.get("px", 0))
        size = float(tr.get("sz", 0))
        side = tr.get("side", "buy")
        evt = self.normalize_trade({"price": price, "size": size, "side": side})
        self.bus.publish(evt)

    def _run_mock(self) -> None:
        depth = int(self.settings.get("dom_depth", 20) or 20)
        while self._running:
            mid = 100 + random.random()
            dom = []
            for i in range(depth // 2):
                price_bid = mid - 0.02 * (i + 1)
                price_ask = mid + 0.02 * (i + 1)
                dom.append({"price": price_bid, "bid_size": random.randint(5, 50), "ask_size": 0})
                dom.append({"price": price_ask, "bid_size": 0, "ask_size": random.randint(5, 50)})
            trade = {"price": mid, "size": random.randint(1, 8), "side": random.choice(["buy", "sell"])}
            self.bus.publish(self.normalize_dom({"dom": dom, "last": mid}))
            self.bus.publish(self.normalize_trade(trade))
            time.sleep(0.2)

    def normalize_dom(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        dom = raw.get("dom", [])
        ladder = {str(level["price"]): {"bid": level.get("bid_size", 0.0), "ask": level.get("ask_size", 0.0)} for level in dom}
        payload = {"dom": dom, "ladder": ladder, "last": raw.get("last")}
        if self.debug:
            import logging
            logging.getLogger(__name__).debug("[OKXProvider] normalize_dom raw=%s payload=%s", raw, payload)
        return MarketEvent(event_type="dom_snapshot", timestamp=ts, source="okx", symbol=self.symbol, payload=payload)

    def normalize_trade(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        evt = MarketEvent(
            event_type="trade",
            timestamp=ts,
            source="okx",
            symbol=self.symbol,
            payload={
                "price": raw.get("price"),
                "size": raw.get("size"),
                "side": raw.get("side", "unknown"),
            },
        )
        if self.debug:
            import logging
            logging.getLogger(__name__).debug("[OKXProvider] normalize_trade raw=%s evt=%s", raw, evt)
        return evt
