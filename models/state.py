from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DOMLevelState:
    price: float
    size: float
    market_maker: Optional[str] = None


@dataclass
class DOMState:
    bids: Dict[int, DOMLevelState] = field(default_factory=dict)
    asks: Dict[int, DOMLevelState] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, List[Dict[str, float]]]:
        return {
            "bids": [{"level": lvl, "price": l.price, "size": l.size} for lvl, l in sorted(self.bids.items())],
            "asks": [{"level": lvl, "price": l.price, "size": l.size} for lvl, l in sorted(self.asks.items())],
        }


@dataclass
class DeltaBar:
    buys: float = 0.0
    sells: float = 0.0
    volume: float = 0.0


@dataclass
class SymbolState:
    dom: DOMState = field(default_factory=DOMState)
    last_price: Optional[float] = None
    delta_bar: DeltaBar = field(default_factory=DeltaBar)
    tape: List[Dict[str, float]] = field(default_factory=list)
