from core.event_bus import EventBus
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from models.order import OrderRequest, OrderSide, OrderType


def test_execution_routing_symbol_independent():
    bus = EventBus()
    adapter = SimAdapter(bus)
    router = ExecutionRouter(bus, adapter)
    order = OrderRequest(
        order_id="o1",
        symbol="EXEC_SYMBOL",
        side=OrderSide.BUY,
        quantity=1.0,
        order_type=OrderType.MARKET,
    )
    router.submit(order)
    bus.stop()
    assert router.orders["o1"].symbol == "EXEC_SYMBOL"
