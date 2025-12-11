from __future__ import annotations

import random
import time
import threading
import asyncio
import json
import logging
import websockets
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
        self._failures = 0
        self._best_bid = None
        self._best_ask = None
        self._last_msg = time.time()
        self._backoff = 1.0
        self._running = False

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
                        self._last_msg = time.time()
                        self._backoff = 1.0
                        handler(data)
            except Exception as exc:
                self._failures += 1
                logging.getLogger(__name__).warning("Binance WS reconnecting after error: %s (fail=%s)", exc, self._failures)
                if self._failures >= 3:
                    logging.getLogger(__name__).error("Binance WS failed 3 times; falling back to mock provider.")
                    self._start_thread(self._run_mock)
                    return
                await asyncio.sleep(min(10.0, self._backoff))
                self._backoff = min(10.0, self._backoff * 2)

    def _run_ws(self) -> None:
        if not self._loop:
            return
        asyncio.set_event_loop(self._loop)
        self._running = True
        logging.getLogger(__name__).info("[Provider] Binance WS connecting for %s", self.symbol)
        stream = self.symbol.lower()
        depth_url = f"wss://stream.binance.com/ws/{stream}@depth20@100ms"
        trade_url = f"wss://stream.binance.com/ws/{stream}@aggTrade"
        ticker_url = f"wss://stream.binance.com/ws/{stream}@ticker"
        book_url = f"wss://stream.binance.com/ws/{stream}@bookTicker"
        self._ws_tasks = [
            self._loop.create_task(self._ws_consume(depth_url, self._handle_depth)),
            self._loop.create_task(self._ws_consume(trade_url, self._handle_trade)),
            self._loop.create_task(self._ws_consume(ticker_url, self._handle_ticker)),
            self._loop.create_task(self._ws_consume(book_url, self._handle_book)),
            self._loop.create_task(self._heartbeat_watch()),
        ]
        self._loop.run_forever()

    async def _heartbeat_watch(self) -> None:
        while self._running:
            await asyncio.sleep(5.0)
            if time.time() - self._last_msg > 10.0:
                logging.getLogger(__name__).warning("Binance WS stale; reconnecting")
                self._failures += 1
                self._backoff = min(10.0, self._backoff * 2)
                self._running = False
                # stop loop to force reconnect
                self._loop.call_soon_threadsafe(self._loop.stop)
                return

    def _handle_depth(self, data: dict) -> None:
        bids = data.get("bids") or data.get("b", [])
        asks = data.get("asks") or data.get("a", [])
        dom = []
        for p, s, *_ in bids:
            dom.append({"price": float(p), "bid_size": float(s), "ask_size": 0.0})
        for p, s, *_ in asks:
            dom.append({"price": float(p), "bid_size": 0.0, "ask_size": float(s)})
        last = self._best_bid if self._best_bid and self._best_ask else None
        evt = self.normalize_dom({"dom": dom, "last": last})
        self.bus.publish(evt)

    def _handle_trade(self, data: dict) -> None:
        price = float(data.get("p", data.get("price", 0)))
        size = float(data.get("q", data.get("size", 0)))
        side = "sell" if data.get("m", True) else "buy"  # aggTrade: m true means buyer is maker
        evt = self.normalize_trade({"price": price, "size": size, "side": side})
        self.bus.publish(evt)

    def _handle_book(self, data: dict) -> None:
        bid = data.get("b")
        ask = data.get("a")
        try:
            self._best_bid = float(bid)
            self._best_ask = float(ask)
        except Exception:
            pass

    def _handle_ticker(self, data: dict) -> None:
        payload = {
            "last": float(data.get("c", 0.0)),
            "change": float(data.get("P", 0.0)),
            "volume": float(data.get("v", 0.0)),
            "provider": "binance",
        }
        evt = MarketEvent(
            event_type="quote",
            timestamp=datetime.now(timezone.utc),
            source="binance",
            symbol=self.symbol,
            payload=payload,
        )
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
                "side": self._side_from_book(raw),
            },
        )
        if self.debug:
            import logging
            logging.getLogger(__name__).debug("[BinanceProvider] normalize_trade raw=%s evt=%s", raw, evt)
        return evt

    def _side_from_book(self, raw: Any) -> str:
        side = raw.get("side")
        if side:
            return side
        price = raw.get("price")
        try:
            p = float(price)
            if self._best_ask and p >= self._best_ask:
                return "buy"
            if self._best_bid and p <= self._best_bid:
                return "sell"
        except Exception:
            pass
        return "unknown"
