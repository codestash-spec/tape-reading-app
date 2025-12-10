from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from core.event_bus import EventBus
from execution.smart_router.slicing import slice_order
from execution.smart_router.queue_time import estimate_queue_time
from execution.smart_router.metrics import ExecutionMetrics
from models.market_event import MarketEvent
from models.order import OrderEvent, OrderRequest, OrderStatus
from execution.router import ExecutionRouter


class SmartOrderRouter:
    """
    High-level router that slices orders, estimates queue times, and delegates to adapters via ExecutionRouter.
    """

    def __init__(self, bus: EventBus, base_router: ExecutionRouter, default_clip: float = 1.0) -> None:
        self.bus = bus
        self.base_router = base_router
        self.default_clip = default_clip
        self.metrics = ExecutionMetrics()
        self.callbacks: Dict[str, Callable[[OrderEvent], None]] = {}
        self.bus.subscribe("order_event", self.on_order_event)

    def route(self, order: OrderRequest, queue_position: float = 0.5) -> List[str]:
        slices = slice_order(order, self.default_clip)
        order_ids: List[str] = []
        for child in slices:
            eta = estimate_queue_time(child, queue_position)
            child.metadata = {**child.metadata, "eta_sec": str(eta)}
            order_ids.append(child.order_id)
            self.base_router.submit(child)
        return order_ids

    def on_order_event(self, evt: MarketEvent) -> None:
        payload = evt.payload or {}
        status = payload.get("status")
        order_id = payload.get("order_id")
        if status not in (OrderStatus.FILL, OrderStatus.PARTIAL.value, "fill", "partial_fill"):
            return
        slippage_bps = float(payload.get("slippage_bps", 0.0))
        latency_ms = float(payload.get("latency_ms", 0.0))
        self.metrics.record_fill(evt.symbol, slippage_bps, latency_ms)

    def cancel_replace(self, order_id: str, new_price: Optional[float] = None) -> None:
        evt = MarketEvent(
            event_type="router_action",
            timestamp=datetime.now(timezone.utc),
            source="smart_router",
            symbol="",
            payload={"order_id": order_id, "action": "cancel_replace", "price": new_price},
        )
        self.bus.publish(evt)
        self.base_router.cancel(order_id)
        if new_price is not None:
            # simplistic replace: not retaining original qty in this stub
            pass

    def peg_order(self, order: OrderRequest, peg: str = "mid") -> OrderRequest:
        if peg == "mid" and order.limit_price and order.stop_price is None:
            order.limit_price = order.limit_price
        return order

    def health(self) -> Dict[str, float]:
        return {"routers": 1, "fills": sum(v.get("fills", 0) for v in self.metrics.stats.values())}
