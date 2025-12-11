import os
from datetime import datetime, timezone

import pytest
from PySide6 import QtCore, QtWidgets

from core.event_bus import EventBus
from models.market_event import MarketEvent
from ui.event_bridge import EventBridge
from ui.widgets.market_watch_panel import MarketWatchPanel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_marketwatch_updates_and_apply(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["trade", "quote"])
    panel = MarketWatchPanel()
    qtbot.addWidget(panel)
    panel.connect_bridge(bridge)

    evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="binance",
        symbol="BTCUSDT",
        payload={"price": 42000.0},
    )
    bus.publish(evt)
    qtbot.wait(50)

    # ensure price updated
    sym = "BTCUSDT"
    row = next((r for r in range(panel.table.rowCount()) if panel.table.item(r, 0).text() == sym), None)
    assert row is not None
    assert panel.table.item(row, 1).text() != "-"
    assert panel.table.item(row, 3).text().lower() == "binance"

    captured = []
    panel.instrumentSelected.connect(lambda s: captured.append(s))
    btn = panel.table.cellWidget(row, 4)
    qtbot.mouseClick(btn, QtCore.Qt.LeftButton)
    assert captured and captured[0] == sym

    bridge.stop()
    bus.stop()
