from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from models.market_event import MarketEvent
from pydantic import ValidationError


def test_aliases_and_immutability():
    """MarketEvent accepts alias fields and remains immutable."""
    ts = datetime.now(timezone.utc)
    evt = MarketEvent(type="tick", ts=ts, source="ibkr", symbol="ES", payload={"price": 10})

    assert evt.event_type == "tick"
    assert evt.timestamp == ts
    assert evt.symbol == "ES"
    with pytest.raises((TypeError, ValidationError)):
        evt.symbol = "NQ"  # type: ignore[misc]


def test_sorting_orders_by_timestamp():
    """MarketEvents should be orderable by timestamp for replay/backfill uses."""
    now = datetime.now(timezone.utc)
    e1 = MarketEvent(event_type="tick", timestamp=now, source="x", symbol="A", payload={})
    e2 = MarketEvent(event_type="tick", timestamp=now + timedelta(seconds=1), source="x", symbol="A", payload={})

    events = sorted([e2, e1], key=lambda e: e.timestamp)
    assert events[0] is e1
