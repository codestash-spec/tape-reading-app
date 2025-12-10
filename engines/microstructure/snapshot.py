from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class MicrostructureSnapshot:
    """
    Aggregated microstructure view combining DOM, tape, delta and footprint signals.
    Designed to be published on the EventBus with event_type="microstructure".
    """

    symbol: str
    timestamp: datetime
    mid: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    imbalance: Optional[float] = None
    queue_position: Optional[float] = None
    liquidity_map: Dict[str, float] = field(default_factory=dict)
    delta: Optional[float] = None
    cumulative_delta: Optional[float] = None
    zero_prints: int = 0
    aggressor_side: Optional[str] = None
    absorption_score: float = 0.0
    footprint: Dict[float, Dict[str, float]] = field(default_factory=dict)
    liquidity_signals: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
