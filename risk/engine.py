from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Dict

from models.order import OrderRequest
from models.risk import RiskDecision


class RiskEngine:
    """
    Simple risk engine with whitelist, size, exposure, throttle, kill-switch.
    """

    def __init__(self, limits: Dict[str, object]) -> None:
        self.limits = limits
        self.kill_switch_engaged = False
        self.exposure: Dict[str, float] = {}
        self.throttle_window = 60.0
        self.throttle_max = int(limits.get("throttle_max", 30))
        self._history: Dict[str, list[float]] = {}

    def engage_kill_switch(self) -> None:
        self.kill_switch_engaged = True

    def reset_kill_switch(self) -> None:
        self.kill_switch_engaged = False

    def _check_throttle(self, symbol: str) -> bool:
        now = time.time()
        hist = self._history.setdefault(symbol, [])
        hist[:] = [t for t in hist if now - t <= self.throttle_window]
        allowed = len(hist) < self.throttle_max
        if allowed:
            hist.append(now)
        return allowed

    def evaluate(self, order: OrderRequest, account_ctx: Dict[str, float] | None = None) -> RiskDecision:
        reasons: list[str] = []
        approved = True

        # kill switch
        if self.kill_switch_engaged:
            approved = False
            reasons.append("kill_switch")

        # symbol whitelist
        symbols = self.limits.get("symbols", [])
        if symbols and order.symbol not in symbols:
            approved = False
            reasons.append("symbol_not_allowed")

        # size limit
        max_size = float(self.limits.get("max_size", float("inf")))
        if order.quantity > max_size:
            approved = False
            reasons.append("size_limit")

        # exposure
        max_exposure = float(self.limits.get("max_exposure", float("inf")))
        current = self.exposure.get(order.symbol, 0.0)
        if abs(current + order.quantity) > max_exposure:
            approved = False
            reasons.append("exposure_limit")

        # throttle
        if not self._check_throttle(order.symbol):
            approved = False
            reasons.append("throttle_exceeded")

        decision = RiskDecision(
            decision_id=uuid.uuid4().hex,
            timestamp=datetime.now(timezone.utc),
            order_id=order.order_id,
            symbol=order.symbol,
            approved=approved,
            reasons=reasons,
            limits={
                "max_size": max_size,
                "max_exposure": max_exposure,
                "throttle_max": self.throttle_max,
            },
        )

        if approved:
            self.exposure[order.symbol] = current + order.quantity * (1 if order.side.value == "buy" else -1)
        return decision
