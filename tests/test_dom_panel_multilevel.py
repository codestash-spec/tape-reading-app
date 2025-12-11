import pytest
from PySide6 import QtWidgets, QtCore

from ui.widgets.dom_panel import DomPanel
from ui.event_bridge import EventBridge
from core.event_bus import EventBus
from models.market_event import MarketEvent


@pytest.mark.qt
def test_dom_panel_accepts_list_and_dict(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot"])
    panel = DomPanel()
    panel.connect_bridge(bridge)
    now = QtCore.QDateTime.currentDateTimeUtc().toPython()
    evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=now,
        source="test",
        symbol="ES",
        payload={"ladder": {"100.0": {"bid": 5, "ask": 0}, "100.1": {"bid": 0, "ask": 6}}},
    )
    bus.publish(evt)
    qtbot.wait(50)
    evt2 = MarketEvent(
        event_type="dom_snapshot",
        timestamp=now,
        source="test",
        symbol="ES",
        payload={"dom": [{"price": 99.9, "bid_size": 10, "ask_size": 0}, {"price": 100.2, "bid_size": 0, "ask_size": 9}]},
    )
    bus.publish(evt2)
    qtbot.wait(50)
    bus.stop()
    assert len(panel.model.rows) >= 2
