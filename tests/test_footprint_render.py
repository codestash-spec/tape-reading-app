import os

import pytest
from PySide6 import QtWidgets

from ui.widgets.footprint_panel import FootprintPanel

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_footprint_renders(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    panel = FootprintPanel()
    qtbot.addWidget(panel)
    panel.queue_footprint({100.0: {"buy": 10, "sell": 5}})
    qtbot.wait(50)
    assert panel._pending is None or panel._pending == {100.0: {"buy": 10, "sell": 5}}
