from __future__ import annotations

from models.order import OrderRequest


def within_price_collar(order: OrderRequest, reference_price: float, collar_bps: float) -> bool:
    if order.limit_price is None:
        return True
    diff_bps = abs(order.limit_price - reference_price) / max(reference_price, 1e-9) * 10000
    return diff_bps <= collar_bps
