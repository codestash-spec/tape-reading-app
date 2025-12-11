import time

from core.event_bus import EventBus
from models.market_event import MarketEvent
from datetime import datetime, timezone


def test_event_bus_throughput():
    bus = EventBus()
    count = 0

    def cb(evt):
        nonlocal count
        count += 1

    bus.subscribe("tick", cb)
    start = time.time()
    for _ in range(5000):
        bus.publish(MarketEvent(event_type="tick", timestamp=datetime.now(timezone.utc), source="perf", symbol="ES", payload={}))
    time.sleep(0.5)
    bus.stop()
    duration = time.time() - start
    assert count == 5000
    assert duration < 2.0  # basic performance guard
