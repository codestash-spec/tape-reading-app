import os

import pytest
from PySide6 import QtWidgets

from ui.widgets.heatmap_panel import HeatmapPanel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_heatmap_renders(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    panel = HeatmapPanel()
    qtbot.addWidget(panel)
    panel._on_dom(type("evt", (), {"payload": {"dom": [{"price": 100.0, "bid_size": 10, "ask_size": 5}]}}))
    qtbot.wait(50)
    assert panel.ladder
