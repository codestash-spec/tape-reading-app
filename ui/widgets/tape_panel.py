from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Any

from PySide6 import QtCore, QtGui, QtWidgets

from ui.event_bridge import EventBridge
from ui.themes import brand


class TapeTableModel(QtCore.QAbstractTableModel):
    HEADERS = ["Time", "Price", "Size", "CumSize", "Side", "Flags"]

    def __init__(self, max_rows: int = 2000) -> None:
        super().__init__()
        self.rows: Deque[list] = deque(maxlen=max_rows)
        self.cum_size: float = 0.0

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
        col = index.column()
        if role == QtCore.Qt.DisplayRole:
            return row[col]
        if role == QtCore.Qt.UserRole:
            return row
        return None

    def append(self, trade: Dict[str, Any]) -> None:
        ts = trade.get("ts") or trade.get("time") or ""
        try:
            price = f"{float(trade.get('price', 0.0)):.3f}"
        except Exception:
            price = str(trade.get("price", ""))
        try:
            size = float(trade.get("size", 0.0))
        except Exception:
            size = 0.0
        self.cum_size += size
        side = trade.get("side", trade.get("aggressor", "?"))
        flags = trade.get("flags", "")
        row = [ts, price, f"{size:.0f}", f"{self.cum_size:.0f}", side, flags]
        self.beginResetModel()
        self.rows.appendleft(row)
        self.endResetModel()


class TapeDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:  # type: ignore[override]
        data = index.data(QtCore.Qt.UserRole)
        if not data:
            super().paint(painter, option, index)
            return
        _, _, size, side, _ = data
        try:
            size_f = float(size)
        except Exception:
            size_f = 0.0
        side_color = QtGui.QColor("#36d399") if side == "buy" else QtGui.QColor("#ff5f56")
        side_color.setAlphaF(0.2 + 0.6 * min(1.0, size_f / 50.0))
        painter.save()
        painter.fillRect(option.rect, side_color)
        painter.setPen(QtGui.QPen(QtGui.QColor(brand.TEXT_LIGHT)))
        painter.drawText(option.rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, str(index.data()))
        painter.restore()


class TapePanel(QtWidgets.QWidget):
    """
    Advanced Time & Sales with color-coded side and size heat.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = TapeTableModel(max_rows=2000)
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(TapeDelegate(self.view))
        self.view.setFont(QtGui.QFont(brand.FONT_FAMILY, brand.FONT_MEDIUM))
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)

        self.speed_bar = QtWidgets.QProgressBar()
        self.speed_bar.setRange(0, 100)
        self.speed_bar.setFormat("Tape Speed %p%")

        # filters
        self.filter_size = QtWidgets.QDoubleSpinBox()
        self.filter_size.setMaximum(1e9)
        self.filter_size.setDecimals(0)
        self.filter_size.setPrefix("Min size ")
        self.filter_side = QtWidgets.QComboBox()
        self.filter_side.addItems(["all", "buy", "sell"])

        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(self.filter_size)
        filter_layout.addWidget(self.filter_side)
        filter_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(filter_layout)
        layout.addWidget(self.speed_bar)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self._recent_sizes: Deque[float] = deque(maxlen=50)
        self._pending: list[Dict[str, Any]] = []
        self._throttle = QtCore.QTimer(self)
        self._throttle.setInterval(int(1000 / 60))
        self._throttle.timeout.connect(self._flush)
        self._throttle.start()
        self._best_bid: float | None = None
        self._best_ask: float | None = None

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.tapeUpdated.connect(self.queue_trade)
        bridge.domUpdated.connect(self._on_dom)

    def _on_dom(self, dom: Dict[str, Any]) -> None:
        ladder = dom.get("ladder") or dom.get("dom") or dom.get("levels") or []
        best_bid = None
        best_ask = None
        if isinstance(ladder, dict):
            for price, entry in ladder.items():
                try:
                    p = float(price)
                    b = float(entry.get("bid", 0.0))
                    a = float(entry.get("ask", 0.0))
                    if b > 0 and (best_bid is None or p > best_bid):
                        best_bid = p
                    if a > 0 and (best_ask is None or p < best_ask):
                        best_ask = p
                except Exception:
                    continue
        elif isinstance(ladder, list):
            for level in ladder:
                try:
                    p = float(level.get("price"))
                    b = float(level.get("bid", level.get("bid_size", 0.0)))
                    a = float(level.get("ask", level.get("ask_size", 0.0)))
                    if b > 0 and (best_bid is None or p > best_bid):
                        best_bid = p
                    if a > 0 and (best_ask is None or p < best_ask):
                        best_ask = p
                except Exception:
                    continue
        self._best_bid = best_bid
        self._best_ask = best_ask

    def queue_trade(self, trade: Dict[str, Any]) -> None:
        side = trade.get("side") or trade.get("aggressor") or self._infer_side(trade)
        try:
            size = float(trade.get("size", 0.0))
        except Exception:
            size = 0.0
        # filters
        if size < self.filter_size.value():
            return
        if self.filter_side.currentText() != "all" and side != self.filter_side.currentText():
            return
        trade["_size_float"] = size
        self._pending.append(trade)

    def _flush(self) -> None:
        from ui.widgets.dom_panel import UI_UPDATE_PAUSED

        if UI_UPDATE_PAUSED or not self._pending:
            return
        batch = self._pending[:]
        self._pending.clear()
        if not batch:
            return
        self.model.beginResetModel()
        for trade in batch:
            size = trade.get("_size_float", 0.0)
            self.model.cum_size += size
            self.model.rows.appendleft(
                [
                    trade.get("ts") or trade.get("time") or "",
                    f"{float(trade.get('price', 0.0)):.3f}" if isinstance(trade.get("price", None), (int, float)) else trade.get("price", ""),
                    f"{size:.0f}",
                    f"{self.model.cum_size:.0f}",
                    trade.get("side", trade.get("aggressor", "?")),
                    trade.get("flags", ""),
                ]
            )
            self._recent_sizes.append(size)
        self.model.endResetModel()
        if self._recent_sizes:
            avg_speed = sum(self._recent_sizes) / len(self._recent_sizes)
            self.speed_bar.setValue(min(100, int(avg_speed)))

    def _infer_side(self, trade: Dict[str, Any]) -> str:
        try:
            price = float(trade.get("price", 0.0))
        except Exception:
            return "unknown"
        if self._best_ask and price >= self._best_ask:
            return "buy"
        if self._best_bid and price <= self._best_bid:
            return "sell"
        return "unknown"
