from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Any

from core.event_bus import EventBus
from models.market_event import MarketEvent


class VolumeProfileEngine:
    """
    Maintains volume histogram per price; computes POC and Value Area.
    Emits volume_profile_update events.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.hist: Dict[str, Dict[float, float]] = defaultdict(dict)
        self.bus.subscribe("trade", self.on_trade)
        self._subs = ("trade",)

    def stop(self) -> None:
        for et in getattr(self, "_subs", ()):
            self.bus.unsubscribe(et, self.on_trade)

    def on_trade(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        payload = evt.payload or {}
        try:
            price = float(payload.get("price", 0.0))
            size = float(payload.get("size", 0.0))
        except Exception:
            return
        book = self.hist.setdefault(sym, {})
        book[price] = book.get(price, 0.0) + size
        self._emit(sym)

    def _emit(self, sym: str) -> None:
        book = self.hist.get(sym, {})
        if not book:
            return
        poc_price = max(book, key=lambda p: book[p])
        total = sum(book.values())
        sorted_prices = sorted(book.keys())
        cum = 0.0
        value_area = []
        for p in sorted_prices:
            cum += book[p]
            value_area.append(p)
            if cum >= 0.7 * total:
                break
        payload: Dict[str, Any] = {
            "histogram": book,
            "poc": poc_price,
            "value_area": value_area,
            "total_volume": total,
        }
        evt = MarketEvent(
            event_type="volume_profile_update",
            timestamp=datetime.now(timezone.utc),
            source="volume_profile",
            symbol=sym,
            payload=payload,
        )
        self.bus.publish(evt)
