from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent


class VolatilityEngine:
    """
    Real-time ATR-like measurement and expansion/compression detection.
    Emits volatility_update events.
    """

    def __init__(self, bus: EventBus, window: int = 50) -> None:
        self.bus = bus
        self.window = window
        self.prices: Dict[str, Deque[float]] = {}
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
        except Exception:
            return
        dq = self.prices.setdefault(sym, deque(maxlen=self.window))
        dq.append(price)
        if len(dq) < 2:
            return
        atr = max(dq) - min(dq)
        regime = "compression" if atr < 0.2 else "expansion" if atr > 1.0 else "normal"
        evt_out = MarketEvent(
            event_type="volatility_update",
            timestamp=datetime.now(timezone.utc),
            source="volatility",
            symbol=sym,
            payload={"atr": atr, "regime": regime},
        )
        self.bus.publish(evt_out)
