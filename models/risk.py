from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class RiskDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    decision_id: str
    timestamp: datetime
    order_id: str
    symbol: str
    approved: bool
    reasons: List[str] = Field(default_factory=list)
    limits: Dict[str, float] = Field(default_factory=dict)
