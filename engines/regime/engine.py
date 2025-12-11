from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent


class RegimeEngine:
    """
    Classifies market into simple regimes based on volatility and delta.
    Emits regime_update events.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.bus.subscribe("volatility_update", self.on_vol)
        self.bus.subscribe("microstructure", self.on_micro)
        self.current_vol: Dict[str, float] = {}
        self._subs = ("volatility_update", "microstructure")

    def stop(self) -> None:
        for et in getattr(self, "_subs", ()):
            if et == "volatility_update":
                self.bus.unsubscribe(et, self.on_vol)
            else:
                self.bus.unsubscribe(et, self.on_micro)

    def on_vol(self, evt: MarketEvent) -> None:
        self.current_vol[evt.symbol] = evt.payload.get("atr", 0.0)

    def on_micro(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        snap = evt.payload.get("snapshot", evt.payload)
        delta = snap.get("cumulative_delta") or snap.get("delta") or 0.0
        vol = self.current_vol.get(sym, 0.0)
        regime = "ranging"
        if vol > 1.0 and abs(delta) > 200:
            regime = "trending"
        elif vol < 0.2:
            regime = "squeezing"
        evt_out = MarketEvent(
            event_type="regime_update",
            timestamp=datetime.now(timezone.utc),
            source="regime_engine",
            symbol=sym,
            payload={"regime": regime, "atr": vol, "delta": delta},
        )
        self.bus.publish(evt_out)
