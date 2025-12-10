from __future__ import annotations

from typing import List

from models.order import OrderRequest


def slice_order(order: OrderRequest, clip_size: float) -> List[OrderRequest]:
    if order.quantity <= clip_size:
        return [order]
    slices: List[OrderRequest] = []
    remaining = order.quantity
    idx = 0
    while remaining > 0:
        qty = min(clip_size, remaining)
        slices.append(
            OrderRequest(
                order_id=f"{order.order_id}-child-{idx}",
                symbol=order.symbol,
                side=order.side,
                quantity=qty,
                order_type=order.order_type,
                limit_price=order.limit_price,
                stop_price=order.stop_price,
                tif=order.tif,
                slippage_bps=order.slippage_bps,
                max_show_size=order.max_show_size,
                post_only=order.post_only,
                reduce_only=order.reduce_only,
                dry_run=order.dry_run,
                routing_hints=order.routing_hints,
                metadata=order.metadata,
            )
        )
        remaining -= qty
        idx += 1
    return slices
