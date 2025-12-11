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
from ui.workspace_manager import WorkspaceManager
from ui.settings_window import SettingsWindow

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_panels_update_models(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot", "trade", "microstructure"])

    dom = DomPanel()
    delta = DeltaPanel()
    fp = FootprintPanel()
    tape = TapePanel()
    dom.connect_bridge(bridge)
    delta.connect_bridge(bridge)
    fp.connect_bridge(bridge)
    tape.connect_bridge(bridge)

    now = QtCore.QDateTime.currentDateTimeUtc().toPython()
    dom_evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=now,
        source="test",
        symbol="ES",
        payload={"ladder": {"100.0": {"bid": 10, "ask": 0}}},
    )
    trade_evt = MarketEvent(event_type="trade", timestamp=now, source="test", symbol="ES", payload={"price": 100.0, "size": 1})
    ms_evt = MarketEvent(
        event_type="microstructure",
        timestamp=now,
        source="test",
        symbol="ES",
        payload={"snapshot": {"cumulative_delta": 5, "footprint": {100.0: {"buy": 1, "sell": 0}}}},
    )
    bus.publish(dom_evt)
    bus.publish(trade_evt)
    bus.publish(ms_evt)
    qtbot.wait(100)
    bus.stop()
    assert dom.model.rows
    assert delta.model.values
    assert fp.model.matrix
    assert tape.model.rows


@pytest.mark.qt
def test_workspace_and_settings(qtbot, tmp_path):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()
    settings = QtCore.QSettings(str(tmp_path / "settings.ini"), QtCore.QSettings.IniFormat)
    manager = WorkspaceManager(win, settings)
    manager.save_profile("test")
    assert manager.load_profile("test") is True

    dlg = SettingsWindow({}, parent=win)
    qtbot.addWidget(dlg)
    dlg.theme_combo.setCurrentText("dark")
    dlg.mode_combo.setCurrentText("sim")
    dlg.log_level.setCurrentText("INFO")
    dlg.apply()
