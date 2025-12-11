from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from providers.provider_base import ProviderBase
from models.market_event import MarketEvent


class IBKRProvider(ProviderBase):
    """
    Placeholder IBKR provider (top-of-book). Uses simulated callbacks; integrate ibapi in future.
    """

    def start(self) -> None:
        # In this placeholder, just emit synthetic best bid/ask less frequently
        self._start_thread(self._run)

    def stop(self) -> None:
        self._stop_thread()

    def subscribe_dom(self) -> None:
        return

    def subscribe_trades(self) -> None:
        return

    def subscribe_quotes(self) -> None:
        return

    def _run(self) -> None:
        price = 100.0
        while self._running:
            price += 0.01
            dom_raw = {"bid": price - 0.01, "ask": price + 0.01, "bid_size": 50, "ask_size": 40}
            trade_raw = {"price": price, "size": 1, "side": "unknown"}
            self.bus.publish(self.normalize_dom(dom_raw))
            self.bus.publish(self.normalize_trade(trade_raw))
            time.sleep(0.5)

    def normalize_dom(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        ladder = {
            str(raw.get("bid", 0.0)): {"bid": raw.get("bid_size", 0.0), "ask": 0.0},
            str(raw.get("ask", 0.0)): {"bid": 0.0, "ask": raw.get("ask_size", 0.0)},
        }
        payload = {
            "dom": [
                {"price": raw.get("bid", 0.0), "bid_size": raw.get("bid_size", 0.0), "ask_size": 0.0},
                {"price": raw.get("ask", 0.0), "bid_size": 0.0, "ask_size": raw.get("ask_size", 0.0)},
            ],
            "ladder": ladder,
            "last": raw.get("bid", 0.0),
        }
        return MarketEvent(event_type="dom_snapshot", timestamp=ts, source="ibkr", symbol=self.symbol, payload=payload)

    def normalize_trade(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        return MarketEvent(
            event_type="trade",
            timestamp=ts,
            source="ibkr",
            symbol=self.symbol,
            payload={
                "price": raw.get("price"),
                "size": raw.get("size"),
                "side": raw.get("side", "unknown"),
            },
        )
