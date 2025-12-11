from models.order import OrderRequest, OrderSide, OrderType
from risk.engine import RiskEngine


def make_order(qty=100, symbol="ES"):
    return OrderRequest(
        order_id="o1",
        symbol=symbol,
        side=OrderSide.BUY,
        quantity=qty,
        order_type=OrderType.MARKET,
    )


def test_risk_kill_switch():
    risk = RiskEngine({"symbols": ["ES"], "max_size": 1000, "max_exposure": 2000, "throttle_max": 5})
    risk.engage_kill_switch()
    dec = risk.evaluate(make_order(10))
    assert dec.approved is False
    assert "kill_switch" in dec.reasons


def test_risk_exposure_and_size():
    risk = RiskEngine({"symbols": ["ES"], "max_size": 50, "max_exposure": 60, "throttle_max": 5})
    dec1 = risk.evaluate(make_order(40))
    assert dec1.approved is True
    dec2 = risk.evaluate(make_order(30))
    assert dec2.approved is False
    assert "exposure_limit" in dec2.reasons or "size_limit" in dec2.reasons


def test_risk_throttle():
    risk = RiskEngine({"symbols": ["ES"], "max_size": 1000, "max_exposure": 2000, "throttle_max": 1})
    dec1 = risk.evaluate(make_order(10))
    dec2 = risk.evaluate(make_order(10))
    assert dec1.approved is True
    assert dec2.approved is False
