from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from models.order import OrderRequest


@dataclass
class QueueIntent:
    join_best: bool = True
    step_in_ticks: int = 0
    prefer_level: int | None = None


class OrderBookRouter:
    """
    Very lightweight queue biasing based on DOM depth.
    """

    def __init__(self) -> None:
        self.bias: Dict[str, QueueIntent] = {}

    def set_bias(self, symbol: str, intent: QueueIntent) -> None:
        self.bias[symbol] = intent

    def apply(self, order: OrderRequest, best_bid: float | None, best_ask: float | None) -> OrderRequest:
        intent = self.bias.get(order.symbol, QueueIntent())
        if order.order_type.value != "limit":
            return order
        price = order.limit_price or (best_bid if order.side.value == "buy" else best_ask)
        if price is None:
            return order
        if intent.step_in_ticks:
            tick = 0.0001
            price = price + tick * intent.step_in_ticks * (1 if order.side.value == "buy" else -1)
        # Return new OrderRequest with adjusted price
        return OrderRequest(**{**order.model_dump(), "limit_price": price})
