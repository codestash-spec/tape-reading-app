from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from models.market_event import MarketEvent


@dataclass
class DeltaState:
    buy: float = 0.0
    sell: float = 0.0
    cumulative: float = 0.0
    zero_prints: int = 0
    last_price: float = 0.0


class MicroDeltaEngine:
    """
    Computes buy/sell delta, cumulative delta and zero-print counts.
    """

    def __init__(self) -> None:
        self.state: Dict[str, DeltaState] = {}

    def on_trade(self, evt: MarketEvent) -> DeltaState:
        payload = evt.payload or {}
        symbol = evt.symbol
        price = float(payload.get("price") or payload.get("last") or 0.0)
        size = float(payload.get("size", payload.get("qty", 0.0)) or 0.0)
        side = payload.get("side") or payload.get("aggressor")
        st = self.state.get(symbol, DeltaState())
        if st.last_price and price == st.last_price:
            st.zero_prints += 1
        st.last_price = price
        if side == "buy" or side == "B":
            st.buy += size
        elif side == "sell" or side == "S":
            st.sell += size
        else:
            # infer aggressor by midpoint comparison if possible
            mid = payload.get("mid")
            if mid is not None:
                if price >= mid:
                    st.buy += size
                else:
                    st.sell += size
        st.cumulative = st.buy - st.sell
        self.state[symbol] = st
        return st
