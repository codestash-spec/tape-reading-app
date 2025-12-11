from __future__ import annotations

from collections import deque
from typing import Dict, Any

from PySide6 import QtWidgets, QtCore

from ui.event_bridge import EventBridge


class StrategySignalsModel(QtCore.QAbstractTableModel):
    HEADERS = ["Time", "Symbol", "Direction", "Score", "Tags"]

    def __init__(self) -> None:
        super().__init__()
        self.rows: deque[list] = deque(maxlen=500)

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self.rows)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:  # type: ignore[override]
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        row = list(self.rows)[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return row[index.column()]
        if role == QtCore.Qt.UserRole:
            return row
        return None

    def append(self, sig: Dict[str, Any]) -> float:
        ts = sig.get("timestamp") or ""
        sym = sig.get("symbol", "")
        dir_ = sig.get("direction", "")
        score = sig.get("score", 0.0)
        tags = sig.get("metadata", {}).get("tags", "") if isinstance(sig.get("metadata"), dict) else ""
        try:
            score_f = float(score)
        except Exception:
            score_f = 0.0
        row = [ts, sym, dir_, f"{score_f:.2f}", tags]
        self.beginResetModel()
        self.rows.appendleft(row)
        self.endResetModel()
        return score_f


class StrategyPanel(QtWidgets.QWidget):
    """
    Shows signals and an opportunity bar based on recent scores.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = StrategySignalsModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)

        self.opportunity = QtWidgets.QProgressBar()
        self.opportunity.setRange(0, 100)
        self.opportunity.setFormat("Opportunity %p%")
        self._recent_scores: deque[float] = deque(maxlen=50)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.opportunity)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.signalGenerated.connect(self.append_signal)

    def append_signal(self, sig: Dict[str, Any]) -> None:
        score = self.model.append(sig)
        self._recent_scores.append(score)
        if self._recent_scores:
            max_abs = max(abs(s) for s in self._recent_scores)
            value = int(min(100, max_abs * 100))
            self.opportunity.setValue(value)
