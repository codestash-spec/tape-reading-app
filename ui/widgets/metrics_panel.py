from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import MetricsModel


class MetricsPanel(QtWidgets.QWidget):
    """
    Displays system metrics.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = MetricsModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.metricsUpdated.connect(self.update_metrics)

    def update_metrics(self, metrics: Dict) -> None:
        self.model.update_metrics(metrics)

