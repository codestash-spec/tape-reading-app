from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import FootprintModel


class FootprintPanel(QtWidgets.QWidget):
    """
    Placeholder footprint heatmap backed by FootprintModel.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = FootprintModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.footprintUpdated.connect(self.update_footprint)
        bridge.microstructureUpdated.connect(self.update_from_snapshot)

    def update_footprint(self, footprint: Dict) -> None:
        self.model.update_footprint(footprint)

    def update_from_snapshot(self, snapshot: Dict) -> None:
        fp = snapshot.get("footprint") or {}
        if fp:
            self.update_footprint(fp)

