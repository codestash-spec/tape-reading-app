import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.microstructure.engine import MicrostructureEngine
from models.market_event import MarketEvent


def test_microstructure_snapshot_generation():
    bus = EventBus()
    engine = MicrostructureEngine(bus, symbols=["ES"])
    engine.start()

    dom_evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"bid": 100.0, "ask": 100.5, "bid_size": 200, "ask_size": 150},
    )
    bus.publish(dom_evt)

    trade_evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"price": 100.25, "size": 10, "side": "buy"},
    )
    bus.publish(trade_evt)
    time.sleep(0.2)
    bus.stop()
