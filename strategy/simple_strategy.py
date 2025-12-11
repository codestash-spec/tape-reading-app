from __future__ import annotations

import logging
from datetime import datetime, timezone

from core.event_bus import EventBus
from models.market_event import MarketEvent


class SimpleStrategyEngine:
    """
    Minimal strategy: reacts to delta updates and emits strategy_signal.
    """

    def __init__(self, bus: EventBus, delta_threshold: float = 50.0) -> None:
        self.bus = bus
        self.delta_threshold = delta_threshold
        self.bus.subscribe("delta_update", self.on_delta)
        self.log = logging.getLogger(__name__)
        self._subs = ("delta_update",)

    def stop(self) -> None:
        for et in getattr(self, "_subs", ()):
            self.bus.unsubscribe(et, self.on_delta)

    def on_delta(self, evt: MarketEvent) -> None:
        payload = evt.payload or {}
        delta = payload.get("delta") or payload.get("cumulative_delta") or 0.0
        try:
            delta_f = float(delta)
        except Exception:
            delta_f = 0.0
        direction = "flat"
        score = 0.0
        reason = "neutral"
        if delta_f >= self.delta_threshold:
            direction = "buy"
            score = delta_f / self.delta_threshold
            reason = "delta_breakout"
        elif delta_f <= -self.delta_threshold:
            direction = "sell"
            score = delta_f / self.delta_threshold
            reason = "delta_breakdown"
        sig = MarketEvent(
            event_type="strategy_signal",
            timestamp=datetime.now(timezone.utc),
            source="simple_strategy",
            symbol=evt.symbol,
            payload={"direction": direction, "score": score, "reason": reason, "delta": delta_f, "timestamp": datetime.now(timezone.utc)},
        )
        self.bus.publish(sig)
