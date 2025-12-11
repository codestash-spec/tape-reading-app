import os
import pytest
from PySide6 import QtWidgets

from ui.widgets.market_watch_panel import MarketWatchPanel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_marketwatch_applies_default(qtbot):
    panel = MarketWatchPanel()
    qtbot.addWidget(panel)
    panel.apply_default_symbol_on_start("BTCUSDT")
    # if symbol exists, initial apply flag set
    assert panel._initial_applied is True
