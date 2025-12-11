import time

import pytest
from PySide6 import QtWidgets, QtCore

from core.event_bus import EventBus
from ui.event_bridge import EventBridge
from ui.widgets.dom_panel import DomPanel
from models.market_event import MarketEvent


@pytest.mark.qt
def test_ui_latency_mock(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot"])
    dom = DomPanel()
    dom.connect_bridge(bridge)
    now = QtCore.QDateTime.currentDateTimeUtc().toPython()

    start = time.time()
    for _ in range(500):
        evt = MarketEvent(
            event_type="dom_snapshot",
            timestamp=now,
            source="SIM",
            symbol="ES",
            payload={"dom": [{"price": 100.0, "bid_size": 1, "ask_size": 0}]},
        )
        bus.publish(evt)
    qtbot.wait(100)
    bus.stop()
    elapsed = time.time() - start
    assert elapsed < 2.0  # basic guard
    assert len(dom.model.rows) > 0
