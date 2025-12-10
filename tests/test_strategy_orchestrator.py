import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from models.market_event import MarketEvent
from strategy.orchestrator import StrategyOrchestrator


def test_strategy_orchestrator_emits_signal():
    bus = EventBus()
    orchestrator = StrategyOrchestrator(bus, symbols=["ES"])
    orchestrator.start()
    snapshot = {
        "features": {"imbalance": 0.2},
        "tags": [],
    }
    evt = MarketEvent(
        event_type="microstructure",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"snapshot": snapshot},
    )
    bus.publish(evt)
    time.sleep(0.2)
    bus.stop()
