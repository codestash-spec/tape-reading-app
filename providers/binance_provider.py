from __future__ import annotations

import random
import time
import threading
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from providers.provider_base import ProviderBase
from models.market_event import MarketEvent


class BinanceProvider(ProviderBase):
    """
    Binance futures depth/trade provider with websocket fallback to mock if websockets unavailable.
    """

    def __init__(self, event_bus, settings, symbol) -> None:
        super().__init__(event_bus, settings, symbol)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ws_tasks = []

    def start(self) -> None:
        try:
            import websockets  # type: ignore

            self._loop = asyncio.new_event_loop()
            t = threading.Thread(target=self._run_ws, daemon=True)
            t.start()
            self._thread = t
        except Exception as exc:
            logging.getLogger(__name__).warning("Binance websockets unavailable (%s); falling back to mock feed", exc)
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

    async def _ws_consume(self, url: str, handler):
        import websockets  # type: ignore

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    async for msg in ws:
                        try:
                            data = json.loads(msg)
                        except Exception:
                            continue
                        handler(data)
            except Exception as exc:
                logging.getLogger(__name__).warning("Binance WS reconnecting after error: %s", exc)
                await asyncio.sleep(1.0)

    def _run_ws(self) -> None:
        if not self._loop:
            return
        asyncio.set_event_loop(self._loop)
        self._running = True
        stream = self.symbol.lower()
        depth_url = f"wss://fstream.binance.com/ws/{stream}@depth20@100ms"
        trade_url = f"wss://fstream.binance.com/ws/{stream}@trade"
        self._ws_tasks = [
            self._loop.create_task(self._ws_consume(depth_url, self._handle_depth)),
            self._loop.create_task(self._ws_consume(trade_url, self._handle_trade)),
        ]
        self._loop.run_forever()

    def _handle_depth(self, data: dict) -> None:
        bids = data.get("b", [])
        asks = data.get("a", [])
        dom = []
        for p, s, *_ in bids:
            dom.append({"price": float(p), "bid_size": float(s), "ask_size": 0.0})
        for p, s, *_ in asks:
            dom.append({"price": float(p), "bid_size": 0.0, "ask_size": float(s)})
        evt = self.normalize_dom({"dom": dom, "last": None})
        self.bus.publish(evt)

    def _handle_trade(self, data: dict) -> None:
        price = float(data.get("p", 0))
        size = float(data.get("q", 0))
        side = "buy" if data.get("m") is False else "sell"
        evt = self.normalize_trade({"price": price, "size": size, "side": side})
        self.bus.publish(evt)

    def _run_mock(self) -> None:
        depth = int(self.settings.get("dom_depth", 20) or 20)
        while self._running:
            mid = 100 + random.random()
            dom = []
            for i in range(depth // 2):
                price_bid = mid - 0.01 * (i + 1)
                price_ask = mid + 0.01 * (i + 1)
                dom.append({"price": price_bid, "bid_size": random.randint(5, 80), "ask_size": 0})
                dom.append({"price": price_ask, "bid_size": 0, "ask_size": random.randint(5, 80)})
            trade = {"price": mid, "size": random.randint(1, 10), "side": random.choice(["buy", "sell"])}
            self.bus.publish(self.normalize_dom({"dom": dom, "last": mid}))
            self.bus.publish(self.normalize_trade(trade))
            time.sleep(0.15)

    def normalize_dom(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        dom = raw.get("dom", [])
        ladder = {str(level["price"]): {"bid": level.get("bid_size", 0.0), "ask": level.get("ask_size", 0.0)} for level in dom}
        payload = {"dom": dom, "ladder": ladder, "last": raw.get("last")}
        if self.debug:
            import logging
            logging.getLogger(__name__).debug("[BinanceProvider] normalize_dom raw=%s payload=%s", raw, payload)
        return MarketEvent(event_type="dom_snapshot", timestamp=ts, source="binance", symbol=self.symbol, payload=payload)

    def normalize_trade(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        evt = MarketEvent(
            event_type="trade",
            timestamp=ts,
            source="binance",
            symbol=self.symbol,
            payload={
                "price": raw.get("price"),
                "size": raw.get("size"),
                "side": raw.get("side", "unknown"),
            },
        )
        if self.debug:
            import logging
            logging.getLogger(__name__).debug("[BinanceProvider] normalize_trade raw=%s evt=%s", raw, evt)
        return evt
