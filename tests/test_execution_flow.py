from datetime import datetime, timezone

from core.event_bus import EventBus
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from models.order import OrderRequest, OrderSide, OrderType


def test_router_and_sim_adapter_publish_events(monkeypatch):
    bus = EventBus()
    adapter = SimAdapter(bus, fill_probability=1.0)
    router = ExecutionRouter(bus, adapter)
    received = []

    def on_order(evt):
        received.append(evt.payload["status"])

    bus.subscribe("order_event", on_order)
    order = OrderRequest(
        order_id="o1",
        symbol="ES",
        side=OrderSide.BUY,
        quantity=1.0,
        order_type=OrderType.LIMIT,
        limit_price=100.0,
    )
    router.submit(order)
    bus.stop()
    assert "ack" in received
    assert any(s in ("fill", "partial_fill", "FILL") for s in received)
