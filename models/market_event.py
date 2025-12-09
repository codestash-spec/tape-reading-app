from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class MarketEvent(BaseModel):
    """
    Universal market event model.
    Standardizes all incoming data into a single schema.

    Providers map their native events (IBKR, dxFeed, Rithmic)
    into this normalized structure before publishing to the EventBus.

    This guarantees that all engines (DOM, Delta, Footprint, Tape)
    can operate with a unified, predictable schema.
    """

    type: str = Field(..., description="Event type: tick, dom, trade, footprint, delta, etc.")
    timestamp: datetime = Field(..., description="Event timestamp in UTC")
    source: str = Field(..., description="Provider identifier: ibkr, dxfeed, rithmic, replay")

    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific structured payload"
    )

    class Config:
        validate_assignment = True
        frozen = True  # Events are immutable → safer & faster
