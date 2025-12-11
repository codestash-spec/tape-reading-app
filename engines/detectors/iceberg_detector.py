from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from core.event_bus import EventBus
from models.market_event import MarketEvent


class IcebergDetector:
    """
    Detects absorption/iceberg patterns: repeated trades at a price without depletion of resting liquidity.
    Emits alert_event with type='iceberg'.
    """

    def __init__(self, bus: EventBus, min_repeats: int = 3, min_size: float = 5.0) -> None:
        self.bus = bus
        self.min_repeats = min_repeats
        self.min_size = min_size
        self.repeats: Dict[str, Dict[float, int]] = {}
        self.bus.subscribe("trade", self.on_trade)

    def on_trade(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        price = evt.payload.get("price")
        size = evt.payload.get("size", 0.0)
        if price is None:
            return
        try:
            p = float(price)
            s = float(size)
        except Exception:
            return
        if s < self.min_size:
            return
        book = self.repeats.setdefault(sym, {})
        book[p] = book.get(p, 0) + 1
        if book[p] >= self.min_repeats:
            self._emit(sym, p, s, book[p])
            book[p] = 0

    def _emit(self, symbol: str, price: float, size: float, repeats: int) -> None:
        evt = MarketEvent(
            event_type="alert_event",
            timestamp=datetime.now(timezone.utc),
            source="iceberg_detector",
            symbol=symbol,
            payload={"type": "iceberg", "price": price, "size": size, "repeats": repeats},
        )
        self.bus.publish(evt)
