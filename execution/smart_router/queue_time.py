from __future__ import annotations

from models.order import OrderRequest


def estimate_queue_time(order: OrderRequest, queue_position: float, avg_fill_rate: float = 100.0) -> float:
    """
    Rough queue time estimation in seconds.
    """
    if avg_fill_rate <= 0:
        return 0.0
    effective_qty = order.quantity * max(queue_position, 0.1)
    return effective_qty / avg_fill_rate
