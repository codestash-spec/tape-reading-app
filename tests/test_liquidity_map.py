from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.liquidity_map.engine import LiquidityMapEngine
from models.market_event import MarketEvent


def test_liquidity_map_emits():
    bus = EventBus()
    engine = LiquidityMapEngine(bus)
    captured = []
    bus.subscribe("liquidity_update", lambda evt: captured.append(evt))
    evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"dom": [{"price": 100.0, "bid_size": 10, "ask_size": 0}]},
    )
    bus.publish(evt)
    bus.stop()
    assert captured and captured[0].event_type == "liquidity_update"
