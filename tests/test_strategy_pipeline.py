from __future__ import annotations

import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.strategy import MicroPriceMomentumStrategy
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from models.market_event import MarketEvent
from models.order import OrderRequest, OrderSide, OrderType
from risk.engine import RiskEngine


def test_strategy_to_execution_pipeline():
    bus = EventBus()
    strategy = MicroPriceMomentumStrategy(bus, symbols=["TEST"], threshold=0.0)
    strategy.on_start()
    risk_engine = RiskEngine({"symbols": ["TEST"], "max_size": 10, "max_exposure": 20, "throttle_max": 10})
    adapter = SimAdapter(bus)
    router = ExecutionRouter(bus, adapter)

    order_events = []

    def on_order(evt: MarketEvent) -> None:
        order_events.append(evt)

    bus.subscribe("order_event", on_order)

    def on_signal(evt: MarketEvent) -> None:
        payload = evt.payload
        side = OrderSide.BUY if payload.get("direction") == "buy" else OrderSide.SELL
        order = OrderRequest(
            order_id="ord-1",
            symbol=evt.symbol,
            side=side,
            quantity=1.0,
            order_type=OrderType.MARKET,
        )
        decision = risk_engine.evaluate(order, account_ctx={})
        if decision.approved:
            router.submit(order)

    bus.subscribe("signal", on_signal)

    tick1 = MarketEvent(
        event_type="tick",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="TEST",
        payload={"mid": 100.0},
    )
    tick2 = MarketEvent(
        event_type="tick",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="TEST",
        payload={"mid": 101.0},
    )
    bus.publish(tick1)
    bus.publish(tick2)
    time.sleep(0.2)
    bus.stop()
    assert order_events, "Expected order events from pipeline"
