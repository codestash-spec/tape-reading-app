from __future__ import annotations

from datetime import datetime, timezone
from typing import Deque, Dict
from collections import deque

from core.event_bus import EventBus
from models.market_event import MarketEvent


class TapeEngine:
    """
    Maintains rolling time and sales (tape) window per symbol.
    """

    def __init__(self, bus: EventBus, max_events: int = 500) -> None:
        self.bus = bus
        self.max_events = max_events
        self.tape: Dict[str, Deque[Dict[str, float]]] = {}
        self.bus.subscribe("trade", self.on_trade)

    def on_trade(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        dq = self.tape.setdefault(sym, deque(maxlen=self.max_events))
        payload = evt.payload
        dq.append(
            {
                "ts": evt.timestamp.timestamp(),
                "price": payload.get("price"),
                "size": payload.get("size"),
                "aggressor": payload.get("aggressor", "unknown"),
            }
        )

    def snapshot(self, symbol: str) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        payload = list(self.tape.get(symbol, deque()))
        return MarketEvent(event_type="tape_snapshot", timestamp=ts, source="tape_engine", symbol=symbol, payload=payload)
