import pytest
from PySide6 import QtWidgets, QtCore

from core.event_bus import EventBus
from models.market_event import MarketEvent
from ui.event_bridge import EventBridge
from ui.widgets.dom_panel import DomPanel


@pytest.mark.qt
def test_dom_data_consistency(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot"])
    dom = DomPanel()
    dom.connect_bridge(bridge)

    now = QtCore.QDateTime.currentDateTimeUtc().toPython()
    payload = {"dom": [{"price": 100.0, "bid_size": 5, "ask_size": 0}, {"price": 100.1, "bid_size": 0, "ask_size": 7}]}
    evt = MarketEvent(event_type="dom_snapshot", timestamp=now, source="test", symbol="ES", payload=payload)
    bus.publish(evt)
    qtbot.wait(50)
    bus.stop()
    assert len(dom.model.rows) == 2
    assert dom.model.rows[0][0] in (100.0, 100.1)
