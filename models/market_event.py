from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class MarketEvent(BaseModel):
    """
    Canonical market event used across the system.

    Providers normalize raw callbacks to this schema before publishing
    to the EventBus so engines can consume a predictable event contract.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        frozen=True,
        extra="ignore",
    )

    event_type: str = Field(
        ...,
        description="Normalized event type: tick, dom_delta, trade, footprint, delta, etc.",
        validation_alias=AliasChoices("event_type", "type"),
    )
    timestamp: datetime = Field(
        ...,
        description="Event timestamp in UTC",
        validation_alias=AliasChoices("timestamp", "ts"),
    )
    source: str = Field(..., description="Provider identifier: ibkr, dxfeed, rithmic, replay")
    symbol: str = Field(..., description="Instrument identifier, e.g. ES, XAUUSD, EURUSD")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Structured payload body")

    @property
    def type(self) -> str:
        """Compatibility alias used by legacy code/tests."""
        return self.event_type
