from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.market_event import MarketEvent


def test_market_event_roundtrip():
    ts = datetime.now(timezone.utc)
    evt = MarketEvent(event_type="tick", timestamp=ts, source="unit", symbol="ES", payload={"price": 10})
    data = evt.model_dump()
    evt2 = MarketEvent(**data)
    assert evt2 == evt
    assert evt2.payload["price"] == 10


def test_market_event_immutability():
    evt = MarketEvent(
        event_type="tick", timestamp=datetime.now(timezone.utc), source="unit", symbol="ES", payload={"p": 1}
    )
    with pytest.raises(TypeError):
        evt.payload = {}


def test_market_event_requires_type():
    with pytest.raises(ValidationError):
        MarketEvent(event_type=None, timestamp=datetime.now(timezone.utc), source="unit", symbol="ES", payload={})
