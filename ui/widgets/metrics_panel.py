from __future__ import annotations

from typing import Dict, Any

from PySide6 import QtCore, QtWidgets, QtGui

from ui.event_bridge import EventBridge
from ui.themes import brand


class MetricsModel(QtCore.QAbstractTableModel):
    HEADERS = ["Metric", "Value"]

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self.rows)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return 2

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            return self.rows[index.row()][index.column()]
        return None

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        self.beginResetModel()
        self.rows = [[k, str(v)] for k, v in metrics.items()]
        self.endResetModel()


class MetricsPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = MetricsModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.setFont(QtGui.QFont(brand.FONT_FAMILY, brand.FONT_SMALL))
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.metricsUpdated.connect(self.update_metrics)
        bridge.microstructureUpdated.connect(self.update_from_snapshot)

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        self.model.update_metrics(metrics)

    def update_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        feats = snapshot.get("features") or {}
        derived = {}
        for key in ("imbalance", "cumulative_delta", "delta", "absorption_score", "zero_prints"):
            if key in snapshot:
                derived[key] = snapshot.get(key)
        derived.update({k: v for k, v in feats.items() if isinstance(v, (int, float))})
        if derived:
            self.model.update_metrics(derived)
