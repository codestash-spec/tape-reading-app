from strategy import pattern_detector
from strategy.confluence import ConfluenceFramework
from strategy.regime import RegimeEngine


def test_pattern_detector():
    assert pattern_detector.classify_pattern({"delta": 600, "shift": 0.1}) == "absorption"
    assert pattern_detector.classify_pattern({"added_liq": 300, "removed_liq": 50}) == "spoof"
    assert pattern_detector.classify_pattern({"imbalance": 0.7, "volume_drop": 60}) == "vacuum"
    assert pattern_detector.classify_pattern({"delta": 400, "price_change": 0.1}) == "divergence"
    assert pattern_detector.classify_pattern({}) == "none"


def test_confluence_framework():
    cf = ConfluenceFramework()
    snap = {"features": {"volatility": 4.0, "liq_spoof": 0}}
    assert cf.validate(snap, snap["features"], []) is True
    snap2 = {"features": {"volatility": 6.0}}
    assert cf.validate(snap2, snap2["features"], []) is False


def test_regime_engine():
    regime = RegimeEngine(atr_threshold=3.0, volume_threshold=10)
    assert regime.is_allowed({"features": {"atr": 2.0, "volume": 20}})
    assert regime.is_allowed({"features": {"atr": 4.0, "volume": 20}}) is False
