import os
import time

import pytest
from PySide6 import QtWidgets
from pyqtgraph.dockarea import DockArea, Dock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_dockarea_moves_fast(qtbot):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    area = DockArea()
    d1 = Dock("d1")
    d2 = Dock("d2")
    area.addDock(d1)
    area.addDock(d2, "bottom", d1)
    qtbot.addWidget(area)
    start = time.time()
    for _ in range(20):
        area.moveDock(d1, "above", d2)
        area.moveDock(d2, "above", d1)
    elapsed = time.time() - start
    assert elapsed < 1.0  # rough bound to catch severe lag
