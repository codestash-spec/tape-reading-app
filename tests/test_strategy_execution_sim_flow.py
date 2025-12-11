from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.delta import DeltaEngine
from models.market_event import MarketEvent
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from strategy.simple_strategy import SimpleStrategyEngine


def test_strategy_to_execution_sim_flow():
    bus = EventBus()
    delta = DeltaEngine(bus)
    strat = SimpleStrategyEngine(bus, delta_threshold=1.0)
    adapter = SimAdapter(bus)
    router = ExecutionRouter(bus, adapter)

    events = []
    bus.subscribe("order_event", lambda e: events.append(e))

    evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="BTCUSDT",
        payload={"price": 100.0, "size": 2.0, "side": "buy"},
    )
    bus.publish(evt)
    # simulate delta update
    bus.publish(
        MarketEvent(
            event_type="delta_update",
            timestamp=datetime.now(timezone.utc),
            source="delta_engine",
            symbol="BTCUSDT",
            payload={"delta": 5.0},
        )
    )
    # strategy_signal should trigger router via on_signal handler in app, but here we directly submit
    # ensure at least one order_event produced via adapter after delta update + strategy
    # allow small delay
    bus.stop()
    assert events
