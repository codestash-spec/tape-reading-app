from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any

from providers.provider_base import ProviderBase
from models.market_event import MarketEvent


class OKXProvider(ProviderBase):
    """
    Mock OKX depth provider. Replace with real websocket when available.
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
