from __future__ import annotations

import threading
from datetime import datetime, timezone

from models.market_event import MarketEvent


def test_publish_and_subscribe(event_bus):
    """EventBus publishes MarketEvents and dispatches to subscribed callbacks."""
    received = []
    signal = threading.Event()

    def on_tick(evt: MarketEvent) -> None:
        received.append(evt)
        signal.set()

    event_bus.subscribe("tick", on_tick)
    event_bus.publish(
        MarketEvent(
            event_type="tick",
            timestamp=datetime.now(timezone.utc),
            source="unit",
            symbol="ES",
            payload={"bid": 10.0, "ask": 10.5},
        )
    )

    assert signal.wait(timeout=1.0)
    assert received[0].payload["bid"] == 10.0


def test_event_without_listener_is_dropped(event_bus, sample_event):
    """EventBus should safely handle events with no subscribers and allow clean stop."""
    event_bus.publish(sample_event)
    event_bus.stop()
    assert not event_bus._running.is_set()
