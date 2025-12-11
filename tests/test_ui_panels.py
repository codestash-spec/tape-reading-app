import os
import pytest
from PySide6 import QtWidgets, QtCore

from core.event_bus import EventBus
from models.market_event import MarketEvent
from ui.event_bridge import EventBridge
from ui.widgets.dom_panel import DomPanel
from ui.widgets.delta_panel import DeltaPanel
from ui.widgets.footprint_panel import FootprintPanel
from ui.widgets.tape_panel import TapePanel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_dom_panel_multilevel(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot", "trade", "microstructure"])
    dom = DomPanel()
    dom.connect_bridge(bridge)
    now = QtCore.QDateTime.currentDateTimeUtc().toPython()
    evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=now,
        source="test",
        symbol="ES",
        payload={"dom": [{"price": 100.0, "bid_size": 10, "ask_size": 0}, {"price": 100.1, "bid_size": 0, "ask_size": 12}]},
    )
    bus.publish(evt)
    qtbot.wait(100)
    bus.stop()
    assert len(dom.model.rows) >= 2


@pytest.mark.qt
def test_delta_footprint_and_tape(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["trade", "microstructure"])
    delta = DeltaPanel()
    fp = FootprintPanel()
    tape = TapePanel()
    delta.connect_bridge(bridge)
    fp.connect_bridge(bridge)
    tape.connect_bridge(bridge)

    now = QtCore.QDateTime.currentDateTimeUtc().toPython()
    trade_evt = MarketEvent(event_type="trade", timestamp=now, source="test", symbol="ES", payload={"price": 100.0, "size": 1, "side": "buy"})
    bus.publish(trade_evt)
    ms_evt = MarketEvent(
        event_type="microstructure",
        timestamp=now,
        source="test",
        symbol="ES",
        payload={"snapshot": {"cumulative_delta": 5, "footprint": {100.0: {"buy": 1, "sell": 0}}}},
    )
    bus.publish(ms_evt)
    qtbot.wait(100)
    bus.stop()
    assert delta.stream
    assert fp.model.matrix
    assert tape.model.rows
