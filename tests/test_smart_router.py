import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from execution.router import ExecutionRouter
from execution.adapters.sim import SimAdapter
from execution.smart_router.router import SmartOrderRouter
from models.order import OrderRequest, OrderSide, OrderType


def test_smart_router_slices_and_routes():
    bus = EventBus()
    adapter = SimAdapter(bus)
    base_router = ExecutionRouter(bus, adapter)
    router = SmartOrderRouter(bus, base_router, default_clip=5)
    order = OrderRequest(
        order_id="o1",
        symbol="ES",
        side=OrderSide.BUY,
        quantity=12,
        order_type=OrderType.LIMIT,
        limit_price=100.0,
    )
    ids = router.route(order, queue_position=0.5)
    assert len(ids) == 3
    time.sleep(0.2)
    bus.stop()
