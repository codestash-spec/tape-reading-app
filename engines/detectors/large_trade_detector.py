from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent


class LargeTradeDetector:
    """
    Flags large trades or sweeps.
    Emits alert_event with type='large_trade'.
    """

    def __init__(self, bus: EventBus, threshold: float = 50.0) -> None:
        self.bus = bus
        self.threshold = threshold
        self.bus.subscribe("trade", self.on_trade)

    def on_trade(self, evt: MarketEvent) -> None:
        payload = evt.payload or {}
        try:
            size = float(payload.get("size", 0.0))
        except Exception:
            return
        if size < self.threshold:
            return
        price = payload.get("price")
        side = payload.get("side", "unknown")
        self._emit(evt.symbol, price, size, side)

    def _emit(self, symbol: str, price, size: float, side: str) -> None:
        evt = MarketEvent(
            event_type="alert_event",
            timestamp=datetime.now(timezone.utc),
            source="large_trade_detector",
            symbol=symbol,
            payload={"type": "large_trade", "price": price, "size": size, "side": side},
        )
        self.bus.publish(evt)
