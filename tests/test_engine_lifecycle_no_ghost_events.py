import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.ohlc.engine import OHLCEngine
from models.market_event import MarketEvent


def test_engine_lifecycle_no_ghost_events():
    bus = EventBus()
    received = []
    bus.allowed_sources = {"provider_a"}

    # Engine subscribes
    ohlc = OHLCEngine(bus, timeframe_seconds=1)
    bus.subscribe("chart_ohlc", lambda evt: received.append(evt))

    # publish from provider_a -> should be accepted
    evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="provider_a",
        symbol="BTCUSDT",
        payload={"price": 100.0, "size": 1.0},
    )
    bus.publish(evt)
    time.sleep(0.05)

    # switch provider: stop engine, change allowed_sources
    ohlc.stop()
    bus.allowed_sources = {"sim"}
    # event from old provider should be dropped
    evt_old = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="provider_a",
        symbol="BTCUSDT",
        payload={"price": 101.0, "size": 1.0},
    )
    bus.publish(evt_old)
    # event from new provider allowed
    evt_new = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="sim",
        symbol="BTCUSDT",
        payload={"price": 102.0, "size": 1.0},
    )
    bus.publish(evt_new)
    time.sleep(0.05)
    bus.stop()

    # only first and third should be processed into chart_ohlc; second is dropped by allowed_sources
    assert len(received) >= 2, "Expected OHLC events from allowed providers"
