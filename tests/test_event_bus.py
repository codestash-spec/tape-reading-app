from __future__ import annotations

import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from models.market_event import MarketEvent


def test_event_bus_dispatch():
    bus = EventBus()
    received = []

    def handler(evt: MarketEvent) -> None:
        received.append(evt)

    bus.subscribe("tick", handler)
    evt = MarketEvent(event_type="tick", timestamp=datetime.now(timezone.utc), source="test", symbol="X", payload={})
    bus.publish(evt)
    time.sleep(0.1)
    bus.stop()
    assert received and received[0].event_type == "tick"
