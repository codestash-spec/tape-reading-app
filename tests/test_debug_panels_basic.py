import os
import pytest
from PySide6 import QtWidgets

from ui.widgets.provider_debug_panel import ProviderDebugPanel
from ui.perf_monitor import FPSMonitor

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.qt
def test_provider_debug_panel_init(qtbot):
    panel = ProviderDebugPanel()
    qtbot.addWidget(panel)
    assert panel.buffer.maxlen == 200


def test_fps_monitor_tick():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    label = FPSMonitor(QtWidgets.QWidget())
    label.tick()
    # no exception means ok
