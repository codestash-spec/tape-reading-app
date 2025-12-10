from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from PySide6 import QtWidgets

from ui.models import DeltaSeriesModel
from ui.event_bridge import EventBridge


class DeltaPanel(QtWidgets.QWidget):
    """
    Displays cumulative delta series.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = DeltaSeriesModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.deltaUpdated.connect(self.update_delta)
        bridge.microstructureUpdated.connect(self.update_from_snapshot)

    def update_delta(self, data: Dict) -> None:
        value = float(data.get("cumulative_delta", data.get("delta", 0.0)) or 0.0)
        self.model.append_delta(datetime.now(timezone.utc), value)

    def update_from_snapshot(self, snapshot: Dict) -> None:
        value = snapshot.get("cumulative_delta") or snapshot.get("delta")
        if value is not None:
            self.update_delta({"cumulative_delta": value})

