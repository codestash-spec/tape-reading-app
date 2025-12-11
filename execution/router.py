from __future__ import annotations

import logging
from typing import Dict

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.order import OrderEvent, OrderRequest

log = logging.getLogger(__name__)


class ExecutionRouter:
    """
    Routes orders to a concrete adapter and publishes order events to the EventBus.
    """

    def __init__(self, bus: EventBus, adapter, mode: str = "SIM") -> None:
        self.bus = bus
        self.adapter = adapter
        self.mode = mode.upper()
        self.orders: Dict[str, OrderRequest] = {}

    def submit(self, order: OrderRequest) -> None:
        self.orders[order.order_id] = order
        log.info(
            "Routing order %s via %s",
            order.order_id,
            self.mode,
            extra={"order_id": order.order_id, "symbol": order.symbol, "mode": self.mode},
        )
        self.adapter.send(order)

    def cancel(self, order_id: str) -> None:
        self.adapter.cancel(order_id)

    def replace(self, order_id: str, new_order: OrderRequest) -> None:
        self.orders[order_id] = new_order
        self.adapter.replace(order_id, new_order)

    def publish_order_event(self, evt: OrderEvent) -> None:
        event = MarketEvent(
            event_type="order_event",
            timestamp=evt.timestamp,
            source="execution",
            symbol=evt.symbol,
            payload=evt.model_dump(),
        )
        self.bus.publish(event)
