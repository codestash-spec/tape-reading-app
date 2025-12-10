from __future__ import annotations

import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from models.market_event import MarketEvent
from models.order import OrderRequest, OrderSide, OrderType


def test_execution_router_with_sim_adapter():
    bus = EventBus()
    adapter = SimAdapter(bus, fill_probability=1.0)
    router = ExecutionRouter(bus, adapter)
    order_events = []

    def on_order(evt: MarketEvent):
        order_events.append(evt)

    bus.subscribe("order_event", on_order)

    order = OrderRequest(
        order_id="ord-sim",
        symbol="TEST",
        side=OrderSide.BUY,
        quantity=1.0,
        order_type=OrderType.MARKET,
    )
    router.submit(order)
    time.sleep(0.1)
    bus.stop()
    assert any(evt.payload["status"] == "fill" for evt in order_events)
