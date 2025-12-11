from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.volume_profile.engine import VolumeProfileEngine
from models.market_event import MarketEvent


def test_volume_profile_poc():
    bus = EventBus()
    engine = VolumeProfileEngine(bus)
    captured = []
    bus.subscribe("volume_profile_update", lambda evt: captured.append(evt.payload))
    evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"price": 100.0, "size": 10},
    )
    bus.publish(evt)
    bus.stop()
    assert captured and captured[0]["poc"] == 100.0
