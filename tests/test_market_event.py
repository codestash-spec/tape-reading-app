from __future__ import annotations

from datetime import datetime, timezone

import pytest

from models.market_event import MarketEvent


def test_market_event_alias_and_immutable():
    evt = MarketEvent(
        event_type="tick",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="X",
        payload={"price": 1.0},
    )
    assert evt.type == "tick"
    with pytest.raises(TypeError):
        evt.symbol = "Y"  # type: ignore[misc]
