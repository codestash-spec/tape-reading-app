from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.detectors.spoofing_detector import SpoofingDetector
from engines.detectors.iceberg_detector import IcebergDetector
from engines.detectors.large_trade_detector import LargeTradeDetector
from models.market_event import MarketEvent


def test_spoofing_detector_emits():
    bus = EventBus()
    det = SpoofingDetector(bus, window=2, ratio=1.5)
    alerts = []
    bus.subscribe("alert_event", lambda evt: alerts.append(evt.payload.get("type")))
    dom1 = MarketEvent("dom_snapshot", datetime.now(timezone.utc), "test", "ES", {"dom": [{"price": 100.0, "bid_size": 10, "ask_size": 5}]})
    dom2 = MarketEvent("dom_snapshot", datetime.now(timezone.utc), "test", "ES", {"dom": [{"price": 100.0, "bid_size": 40, "ask_size": 5}]})
    bus.publish(dom1)
    bus.publish(dom2)
    bus.stop()
    assert "spoof" in alerts


def test_iceberg_detector_emits():
    bus = EventBus()
    det = IcebergDetector(bus, min_repeats=2, min_size=1)
    alerts = []
    bus.subscribe("alert_event", lambda evt: alerts.append(evt.payload.get("type")))
    trade = lambda: MarketEvent("trade", datetime.now(timezone.utc), "test", "ES", {"price": 100.0, "size": 2})
    bus.publish(trade())
    bus.publish(trade())
    bus.stop()
    assert "iceberg" in alerts


def test_large_trade_detector_emits():
    bus = EventBus()
    det = LargeTradeDetector(bus, threshold=5)
    alerts = []
    bus.subscribe("alert_event", lambda evt: alerts.append(evt.payload.get("type")))
    evt = MarketEvent("trade", datetime.now(timezone.utc), "test", "ES", {"price": 100.0, "size": 10})
    bus.publish(evt)
    bus.stop()
    assert "large_trade" in alerts
