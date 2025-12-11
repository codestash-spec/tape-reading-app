from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.order import OrderEvent, OrderRequest, OrderStatus

log = logging.getLogger(__name__)


class SimAdapter:
    """
    Simulated execution adapter for tests and replay.
    """

    def __init__(self, bus: EventBus, fill_probability: float = 1.0) -> None:
        self.bus = bus
        self.fill_probability = fill_probability
        self.orders: Dict[str, OrderRequest] = {}

    def send(self, order: OrderRequest) -> None:
        self.orders[order.order_id] = order
        ack = OrderEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            status=OrderStatus.ACK,
            timestamp=datetime.now(timezone.utc),
            filled_qty=0.0,
        )
        self._publish(ack)
        if random.random() <= self.fill_probability:
            fill = OrderEvent(
                order_id=order.order_id,
                symbol=order.symbol,
                status=OrderStatus.FILL,
                timestamp=datetime.now(timezone.utc),
                filled_qty=order.quantity,
                avg_price=order.limit_price or order.stop_price or 0.0,
            )
            self._publish(fill)

    def cancel(self, order_id: str) -> None:
        evt = OrderEvent(
            order_id=order_id,
            symbol=self.orders.get(order_id).symbol if order_id in self.orders else "",
            status=OrderStatus.CANCEL,
            timestamp=datetime.now(timezone.utc),
        )
        self._publish(evt)

    def replace(self, order_id: str, new_order: OrderRequest) -> None:
        self.orders[order_id] = new_order
        self.send(new_order)

    def _publish(self, evt: OrderEvent) -> None:
        market_evt = MarketEvent(
            event_type="order_event",
            timestamp=evt.timestamp,
            source="execution_sim",
            symbol=evt.symbol,
            payload=evt.model_dump(),
        )
        self.bus.publish(market_evt)
