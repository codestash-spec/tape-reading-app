from __future__ import annotations

from typing import Callable, Dict, Optional, Any

from PySide6 import QtWidgets, QtCore, QtGui

from ui.event_bridge import EventBridge
from ui.themes import brand


class ExecutionOrdersModel(QtCore.QAbstractTableModel):
    HEADERS = ["Order ID", "Symbol", "Side", "Status", "Qty", "AvgPx", "Slippage"]

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list] = []

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
        row = self.rows[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return row[index.column()]
        if role == QtCore.Qt.UserRole:
            return row
        return None

    def upsert(self, evt: Dict[str, Any]) -> None:
        oid = evt.get("order_id", "")
        side = evt.get("side", "")
        status = evt.get("status", "")
        sym = evt.get("symbol", "")
        qty = evt.get("filled_qty", evt.get("quantity", 0.0))
        avg = evt.get("avg_price", evt.get("limit_price", 0.0))
        slip = evt.get("slippage_bps", 0.0)
        try:
            qty_f = float(qty)
        except Exception:
            qty_f = 0.0
        try:
            avg_f = float(avg)
        except Exception:
            avg_f = 0.0
        try:
            slip_f = float(slip)
        except Exception:
            slip_f = 0.0

        new_row = [oid, sym, side, status, f"{qty_f:.2f}", f"{avg_f:.2f}", f"{slip_f:.2f}"]

        existing = next((i for i, r in enumerate(self.rows) if r[0] == oid), None)
        if existing is None:
            self.beginResetModel()
            self.rows.insert(0, new_row)
            self.endResetModel()
        else:
            self.rows[existing] = new_row
            tl = self.index(existing, 0)
            br = self.index(existing, len(self.HEADERS) - 1)
            self.dataChanged.emit(tl, br, [])


class ExecutionDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:  # type: ignore[override]
        row = index.data(QtCore.Qt.UserRole)
        if not row:
            super().paint(painter, option, index)
            return
        side = row[2]
        status = row[3]
        bg = QtGui.QColor(0, 0, 0, 0)
        if side == "buy":
            bg = QtGui.QColor(54, 211, 153, 40)
        elif side == "sell":
            bg = QtGui.QColor(255, 95, 86, 40)
        if status.lower() in ("fill", "filled", "partial_fill"):
            bg.setAlpha(90)
        painter.save()
        if bg.alpha() > 0:
            painter.fillRect(option.rect, bg)
        painter.setPen(QtGui.QPen(QtGui.QColor(brand.TEXT_LIGHT)))
        painter.drawText(option.rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, str(index.data()))
        painter.restore()


class ExecutionPanel(QtWidgets.QWidget):
    """
    Execution blotter with side coloring and slippage/avgPx safe parsing.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = ExecutionOrdersModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(ExecutionDelegate(self.view))
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)

        self.cancel_btn = QtWidgets.QPushButton("Cancel Selected")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)

        info_layout = QtWidgets.QHBoxLayout()
        info_layout.addWidget(self.cancel_btn)
        info_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(info_layout)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self._cancel_callback: Optional[Callable[[str], None]] = None

    def connect_bridge(self, bridge: EventBridge, on_cancel: Optional[Callable[[str], None]] = None) -> None:
        bridge.orderStatusUpdated.connect(self.update_order)
        self._cancel_callback = on_cancel

    def update_order(self, evt: Dict[str, Any]) -> None:
        self.model.upsert(evt)

    def _on_cancel_clicked(self) -> None:
        if not self._cancel_callback:
            return
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        order_id = self.model.rows[idx.row()][0]
        self._cancel_callback(order_id)
