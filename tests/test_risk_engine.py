from __future__ import annotations

from datetime import datetime

from models.order import OrderRequest, OrderSide, OrderType
from risk.engine import RiskEngine


def _order(qty: float) -> OrderRequest:
    return OrderRequest(
        order_id="o",
        symbol="TEST",
        side=OrderSide.BUY,
        quantity=qty,
        order_type=OrderType.MARKET,
    )


def test_risk_limits_and_throttle():
    limits = {"symbols": ["TEST"], "max_size": 5, "max_exposure": 10, "throttle_max": 1}
    risk = RiskEngine(limits)
    ok = risk.evaluate(_order(5), {})
    assert ok.approved
    too_big = risk.evaluate(_order(6), {})
    assert not too_big.approved and "size_limit" in too_big.reasons
    throttle = risk.evaluate(_order(1), {})
    assert not throttle.approved and "throttle_exceeded" in throttle.reasons


def test_risk_exposure_limit():
    limits = {"symbols": ["TEST"], "max_size": 10, "max_exposure": 2, "throttle_max": 10}
    risk = RiskEngine(limits)
    first = risk.evaluate(_order(1.5), {})
    assert first.approved
    second = risk.evaluate(_order(1.0), {})
    assert not second.approved and "exposure_limit" in second.reasons
