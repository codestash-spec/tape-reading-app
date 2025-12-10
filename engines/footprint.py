from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.state import SymbolState


class FootprintEngine:
    """
    Simple footprint accumulator: volume per price level.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.cells: Dict[str, Dict[float, Dict[str, float]]] = {}
        self.state: Dict[str, SymbolState] = {}
        self.bus.subscribe("trade", self.on_trade)

    def on_trade(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        price = float(evt.payload.get("price", 0.0))
        size = float(evt.payload.get("size", 0.0))
        aggressor = evt.payload.get("aggressor", "unknown")

        book = self.cells.setdefault(sym, {})
        cell = book.setdefault(price, {"buy": 0.0, "sell": 0.0, "unknown": 0.0})
        cell[aggressor] = cell.get(aggressor, 0.0) + size

    def snapshot(self, symbol: str) -> MarketEvent:
        ts = datetime.now(timezone.utc)
        book = self.cells.get(symbol, {})
        payload: List[Dict[str, float]] = []
        for price, sides in book.items():
            payload.append({"price": price, **sides})
        return MarketEvent(
            event_type="footprint_snapshot",
            timestamp=ts,
            source="footprint_engine",
            symbol=symbol,
            payload=payload,
        )
