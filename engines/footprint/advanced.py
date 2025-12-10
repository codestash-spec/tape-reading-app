from __future__ import annotations

from collections import defaultdict
from typing import Dict

from models.market_event import MarketEvent


class FootprintEngineAdvanced:
    """
    Maintains per-price footprint (buy/sell volume) and derives imbalances.
    """

    def __init__(self) -> None:
        self.footprints: Dict[str, Dict[float, Dict[str, float]]] = defaultdict(lambda: defaultdict(lambda: {"buy": 0.0, "sell": 0.0}))

    def on_trade(self, evt: MarketEvent) -> Dict[float, Dict[str, float]]:
        payload = evt.payload or {}
        symbol = evt.symbol
        price = float(payload.get("price") or payload.get("last") or 0.0)
        size = float(payload.get("size", payload.get("qty", 0.0)) or 0.0)
        side = payload.get("side") or payload.get("aggressor")
        fp = self.footprints[symbol]
        if side == "buy":
            fp[price]["buy"] += size
        elif side == "sell":
            fp[price]["sell"] += size
        else:
            fp[price]["buy"] += size * 0.5
            fp[price]["sell"] += size * 0.5
        self.footprints[symbol] = fp
        return fp

    def imbalance_heatmap(self, symbol: str) -> Dict[float, float]:
        fp = self.footprints.get(symbol, {})
        return {p: (v.get("buy", 0.0) - v.get("sell", 0.0)) for p, v in fp.items()}
