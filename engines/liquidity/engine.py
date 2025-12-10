from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from models.market_event import MarketEvent


@dataclass
class LiquiditySignals:
    iceberg: float = 0.0
    spoof: float = 0.0
    replenishment: float = 0.0
    shift: float = 0.0


class LiquidityEngine:
    """
    Detects iceberg/replenishment/spoofing style signals from DOM deltas.
    """

    def __init__(self, iceberg_threshold: float = 500.0, spoof_ratio: float = 3.0) -> None:
        self.iceberg_threshold = iceberg_threshold
        self.spoof_ratio = spoof_ratio
        self.state: Dict[str, LiquiditySignals] = {}

    def on_dom_delta(self, evt: MarketEvent) -> LiquiditySignals:
        payload = evt.payload or {}
        symbol = evt.symbol
        added_bid = float(payload.get("added_bid", 0.0) or 0.0)
        removed_bid = float(payload.get("removed_bid", 0.0) or 0.0)
        added_ask = float(payload.get("added_ask", 0.0) or 0.0)
        removed_ask = float(payload.get("removed_ask", 0.0) or 0.0)
        shift = float(payload.get("mid_shift", 0.0) or 0.0)

        sig = LiquiditySignals()
        if removed_bid > self.iceberg_threshold or removed_ask > self.iceberg_threshold:
            sig.iceberg = max(removed_bid, removed_ask) / self.iceberg_threshold
        if added_bid > removed_bid * self.spoof_ratio or added_ask > removed_ask * self.spoof_ratio:
            sig.spoof = 1.0
        if added_bid > 0 and removed_bid == 0:
            sig.replenishment = added_bid / self.iceberg_threshold
        if shift:
            sig.shift = shift
        self.state[symbol] = sig
        return sig
