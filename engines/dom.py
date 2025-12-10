from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.state import DOMLevelState, DOMState

log = logging.getLogger(__name__)


class DOMEngine:
    """
    Maintains in-memory DOM ladder via dom_delta events and emits snapshots.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.books: Dict[str, DOMState] = {}
        self.bus.subscribe("dom_delta", self.on_dom_delta)

    def on_dom_delta(self, evt: MarketEvent) -> None:
        payload = evt.payload
        sym = evt.symbol
        book = self.books.setdefault(sym, DOMState())

        side = payload.get("side")
        level = int(payload.get("level", 0))
        operation = payload.get("operation")
        price = payload.get("price")
        size = payload.get("size")
        market_maker = payload.get("market_maker")

        side_map = book.bids if side == "bid" else book.asks

        if operation == "insert" or operation == "update":
            side_map[level] = DOMLevelState(price=price, size=size, market_maker=market_maker)
        elif operation == "delete":
            side_map.pop(level, None)

    def snapshot(self, symbol: str) -> MarketEvent:
        book = self.books.get(symbol, DOMState())
        ts = datetime.now(timezone.utc)
        payload = book.snapshot()
        return MarketEvent(event_type="dom_snapshot", timestamp=ts, source="dom_engine", symbol=symbol, payload=payload)
