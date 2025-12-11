import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.microstructure.engine import MicrostructureEngine
from models.market_event import MarketEvent
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from risk.engine import RiskEngine
from strategy.orchestrator import StrategyOrchestrator


def test_full_pipeline_signal_to_fill():
    bus = EventBus()
    micro = MicrostructureEngine(bus, symbols=["ES"])
    micro.start()
    strat = StrategyOrchestrator(bus, symbols=["ES"])
    strat.start()
    risk = RiskEngine({"symbols": ["ES"], "max_size": 1000, "max_exposure": 2000, "throttle_max": 10})
    adapter = SimAdapter(bus, fill_probability=1.0)
    router = ExecutionRouter(bus, adapter)

    fills = []

    def on_fill(evt: MarketEvent):
        if evt.payload.get("status") in ("fill", "partial_fill", "FILL"):
            fills.append(evt)

    bus.subscribe("order_event", on_fill)

    dom_evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"bid": 100.0, "ask": 100.5, "bid_size": 200, "ask_size": 150},
    )
    trade_evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"price": 100.25, "size": 10, "side": "buy", "mid": 100.25},
    )

    bus.publish(dom_evt)
    bus.publish(trade_evt)

    time.sleep(0.4)
    bus.stop()
    assert fills, "Expected fills from pipeline"
