from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from models.market_event import MarketEvent


@dataclass
class DepthState:
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: float = 0.0
    ask_size: float = 0.0
    imbalance: float = 0.0
    queue_position: float = 0.0
    liquidity_map: Dict[str, float] = field(default_factory=dict)


class DepthEngine:
    """
    Maintains depth ladder state, computes imbalance and queue position estimates.
    """

    def __init__(self) -> None:
        self.state: Dict[str, DepthState] = {}

    def on_dom(self, evt: MarketEvent) -> DepthState:
        symbol = evt.symbol
        payload = evt.payload or {}
        bid = payload.get("bid")
        ask = payload.get("ask")
        bid_size = float(payload.get("bid_size", payload.get("bid_qty", 0.0)) or 0.0)
        ask_size = float(payload.get("ask_size", payload.get("ask_qty", 0.0)) or 0.0)
        ladder = payload.get("ladder", {})
        my_order_qty = float(payload.get("my_order_qty", 0.0) or 0.0)

        st = self.state.get(symbol, DepthState())
        st.bid = bid if bid is not None else st.bid
        st.ask = ask if ask is not None else st.ask
        st.bid_size = bid_size
        st.ask_size = ask_size
        denom = bid_size + ask_size
        st.imbalance = ((bid_size - ask_size) / denom) if denom else 0.0
        normalized = {}
        for k, v in ladder.items():
            try:
                if isinstance(v, dict):
                    bid_v = float(v.get("bid", 0.0) or 0.0)
                    ask_v = float(v.get("ask", 0.0) or 0.0)
                    normalized[str(k)] = bid_v + ask_v
                else:
                    normalized[str(k)] = float(v)
            except Exception:
                continue
        st.liquidity_map = normalized
        st.queue_position = self._estimate_queue_position(st, my_order_qty)

        self.state[symbol] = st
        return st

    @staticmethod
    def _estimate_queue_position(st: DepthState, my_order_qty: float) -> float:
        if not my_order_qty:
            return 0.0
        ref_size = st.bid_size if my_order_qty > 0 else st.ask_size
        if ref_size <= 0:
            return 1.0
        return min(1.0, my_order_qty / ref_size)
