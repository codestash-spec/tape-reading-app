from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any

from providers.provider_base import ProviderBase
from models.market_event import MarketEvent


class SimProvider(ProviderBase):
    """
    Synthetic provider for simulation/testing.
    """

    def start(self) -> None:
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
        while self._running:
            mid = 100 + random.random()
            bid = mid - 0.05
            ask = mid + 0.05
            dom_raw = {
                "dom": [
                    {"price": bid, "bid_size": random.randint(50, 200), "ask_size": 0},
                    {"price": ask, "bid_size": 0, "ask_size": random.randint(50, 200)},
                ],
                "last": mid,
            }
            trade_raw = {"price": mid, "size": random.randint(1, 20), "side": random.choice(["buy", "sell"])}
            self.bus.publish(self.normalize_dom(dom_raw))
            self.bus.publish(self.normalize_trade(trade_raw))
            time.sleep(0.25)

    def normalize_dom(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        dom = raw.get("dom", [])
        ladder = {str(level["price"]): {"bid": level.get("bid_size", 0.0), "ask": level.get("ask_size", 0.0)} for level in dom}
        payload = {"dom": dom, "ladder": ladder, "last": raw.get("last")}
        return MarketEvent(event_type="dom_snapshot", timestamp=ts, source="sim", symbol=self.symbol, payload=payload)

    def normalize_trade(self, raw: Any) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        return MarketEvent(
            event_type="trade",
            timestamp=ts,
            source="sim",
            symbol=self.symbol,
            payload={
                "price": raw.get("price"),
                "size": raw.get("size"),
                "side": raw.get("side", "unknown"),
            },
        )
