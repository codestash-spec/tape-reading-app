from __future__ import annotations

from typing import Dict, List, Tuple, Any

from PySide6 import QtCore, QtGui, QtWidgets

from ui.event_bridge import EventBridge
from ui.themes import brand


class DomTableModel(QtCore.QAbstractTableModel):
    HEADERS = ["Price", "Bid Size", "Ask Size", "Liquidity"]

    def __init__(self) -> None:
        super().__init__()
        self.rows: List[Tuple[float, float, float, float]] = []
        self.last_price: float | None = None

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
        price, bid, ask, liq = self.rows[index.row()]
        col = index.column()
        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return f"{price:.2f}"
            if col == 1:
                return f"{bid:.0f}"
            if col == 2:
                return f"{ask:.0f}"
            if col == 3:
                return f"{liq:.2f}"
        if role == QtCore.Qt.UserRole:
            return (price, bid, ask, liq)
        return None

    def update_rows(self, rows: List[Tuple[float, float, float, float]], last_price: float | None) -> None:
        self.beginResetModel()
        self.rows = rows
        self.last_price = last_price
        self.endResetModel()


class DomDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model: DomTableModel, parent=None) -> None:
        super().__init__(parent)
        self.model = model

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:  # type: ignore[override]
        value = self.model.data(index, QtCore.Qt.UserRole)
        if not value:
            super().paint(painter, option, index)
            return
        price, bid, ask, liq = value
        col = index.column()
        painter.save()

        bg = QtGui.QColor(0, 0, 0, 0)
        if col == 1:
            intensity = min(1.0, bid / max(1.0, self._max_col(1)))
            bg = QtGui.QColor(18, 216, 250)
            bg.setAlphaF(0.1 + 0.8 * intensity)
        elif col == 2:
            intensity = min(1.0, ask / max(1.0, self._max_col(2)))
            bg = QtGui.QColor(255, 95, 86)
            bg.setAlphaF(0.1 + 0.8 * intensity)

        if self.model.last_price is not None and abs(price - self.model.last_price) < 1e-6:
            bg = QtGui.QColor(255, 215, 0, 50)

        if bg.alpha() > 0:
            painter.fillRect(option.rect, bg)

        painter.setPen(QtGui.QPen(QtGui.QColor(brand.TEXT_LIGHT)))
        painter.drawText(option.rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, str(index.data()))
        painter.restore()

    def _max_col(self, col: int) -> float:
        vals = []
        for _, bid, ask, _ in self.model.rows:
            vals.append(bid if col == 1 else ask)
        return max(vals) if vals else 1.0


class DomPanel(QtWidgets.QWidget):
    """
    DOM ladder with multiple levels, heatmap and last-price highlight.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = DomTableModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(DomDelegate(self.model, self.view))
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.domUpdated.connect(self.update_dom)

    def update_dom(self, payload: Dict[str, Any]) -> None:
        ladder_raw = payload.get("ladder") or payload.get("levels") or []
        last_price = None
        if "last" in payload:
            try:
                last_price = float(payload.get("last"))
            except Exception:
                last_price = None
        rows: List[Tuple[float, float, float, float]] = []

        def add_row(price, bid, ask):
            try:
                p = float(price)
                b = float(bid)
                a = float(ask)
                liq = b - a
                rows.append((p, b, a, liq))
            except Exception:
                return

        if isinstance(ladder_raw, dict):
            for price, entry in ladder_raw.items():
                if isinstance(entry, dict):
                    add_row(price, entry.get("bid", 0.0), entry.get("ask", 0.0))
                else:
                    add_row(price, entry, 0.0)
        elif isinstance(ladder_raw, list):
            for level in ladder_raw:
                if isinstance(level, dict):
                    add_row(level.get("price", 0.0), level.get("bid", 0.0), level.get("ask", 0.0))
                elif isinstance(level, (list, tuple)) and len(level) >= 3:
                    add_row(level[0], level[1], level[2])

        rows = sorted(rows, key=lambda r: r[0], reverse=True)[:50]
        self.model.update_rows(rows, last_price)
