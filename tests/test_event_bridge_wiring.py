import os
import time
from datetime import datetime, timezone

from PySide6 import QtCore, QtTest

from core.event_bus import EventBus
from models.market_event import MarketEvent
from ui.event_bridge import EventBridge

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_event_bridge_emits_signal():
    app = QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot"])

    spy = QtTest.QSignalSpy(bridge.domUpdated)
    evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=datetime.now(timezone.utc),
        source="test",
        symbol="ES",
        payload={"bid": 100.0, "ask": 100.5, "bid_size": 10, "ask_size": 12},
    )
    bus.publish(evt)
    QtTest.QTest.qWait(200)
    bus.stop()

    assert len(spy) >= 1
    # keep app alive briefly to process queued signals
    app.processEvents()
    time.sleep(0.05)
