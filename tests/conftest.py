from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator

import pytest

from core.event_bus import EventBus
from models.market_event import MarketEvent


@pytest.fixture
def event_bus() -> Generator[EventBus, None, None]:
    bus = EventBus()
    yield bus
    bus.stop()


@pytest.fixture
def sample_event() -> MarketEvent:
    return MarketEvent(
        event_type="tick",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="XAUUSD",
        payload={"mid": 1.0},
    )
