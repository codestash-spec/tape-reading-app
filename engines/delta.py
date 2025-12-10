from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.state import DeltaBar, SymbolState


class DeltaEngine:
    """
    Lightweight delta/footprint accumulator from trade events.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.state: Dict[str, SymbolState] = {}
        self.bus.subscribe("trade", self.on_trade)

    def on_trade(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        st = self.state.setdefault(sym, SymbolState())
        payload = evt.payload
        price = float(payload.get("price", 0.0))
        size = float(payload.get("size", 0.0))
        aggressor = payload.get("aggressor", "unknown")

        st.delta_bar.volume += size
        if aggressor == "buy":
            st.delta_bar.buys += size
        elif aggressor == "sell":
            st.delta_bar.sells += size
        st.last_price = price

    def emit_delta(self, symbol: str) -> MarketEvent:
        st = self.state.setdefault(symbol, SymbolState())
        ts = datetime.now(timezone.utc)
        payload = {
            "buys": st.delta_bar.buys,
            "sells": st.delta_bar.sells,
            "volume": st.delta_bar.volume,
            "last_price": st.last_price,
        }
        return MarketEvent(event_type="delta_bar", timestamp=ts, source="delta_engine", symbol=symbol, payload=payload)
