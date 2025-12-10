from __future__ import annotations

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class Signal(BaseModel):
    """
    Strategy signal to be consumed by execution/risk.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    signal_id: str
    timestamp: datetime
    symbol: str
    direction: str  # buy/sell/flat
    score: float = 0.0
    confidence: float = 0.0
    features: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, str] = Field(default_factory=dict)
