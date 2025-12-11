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


UI_UPDATE_PAUSED = False


class DomPanel(QtWidgets.QWidget):
    """
    DOM ladder with multiple levels, heatmap and last-price highlight.
    Includes throttling (60 FPS) and pause during drag/resize.
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
        self.view.viewport().installEventFilter(self)
        # heatmap canvas
        self.heatmap = QtWidgets.QLabel()
        self.heatmap.setMinimumHeight(80)
        self.heatmap.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.heatmap.setStyleSheet("background-color: #0f1b2b; border: 1px solid #1f2b3a;")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        layout.addWidget(self.heatmap)
        self.setLayout(layout)

        self._pending_payload: Dict[str, Any] | None = None
        self._throttle = QtCore.QTimer(self)
        self._throttle.setInterval(int(1000 / 60))  # ~60 FPS
        self._throttle.timeout.connect(self._flush)
        self._throttle.start()

    def eventFilter(self, obj, event):
        global UI_UPDATE_PAUSED
        if event.type() in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseMove):
            UI_UPDATE_PAUSED = True
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            UI_UPDATE_PAUSED = False
        return super().eventFilter(obj, event)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.domUpdated.connect(self.queue_dom)

    def queue_dom(self, payload: Dict[str, Any]) -> None:
        self._pending_payload = payload

    def _flush(self) -> None:
        global UI_UPDATE_PAUSED
        if UI_UPDATE_PAUSED or self._pending_payload is None:
            return
        payload = self._pending_payload
        self._pending_payload = None
        ladder_raw = payload.get("ladder") or payload.get("levels") or payload.get("dom") or []
        last_price = None
        if "last" in payload or "mid" in payload or "price" in payload:
            for key in ("last", "mid", "price"):
                try:
                    if key in payload:
                        last_price = float(payload.get(key))
                        break
                except Exception:
                    continue
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

        rows = sorted(rows, key=lambda r: r[0], reverse=True)[:100]
        self.model.update_rows(rows, last_price)
        self._draw_heatmap(rows)

    def _draw_heatmap(self, rows: List[Tuple[float, float, float, float]]) -> None:
        if not rows:
            return
        h = self.heatmap.height() or 120
        w = self.heatmap.width() or 300
        pix = QtGui.QPixmap(w, h)
        pix.fill(QtGui.QColor(0, 0, 0, 0))
        painter = QtGui.QPainter(pix)
        painter.fillRect(pix.rect(), QtGui.QColor(15, 27, 43))
        max_size = max(max(r[1], r[2]) for r in rows) or 1.0
        row_h = max(2, h // len(rows))
        for i, (price, bid, ask, _) in enumerate(rows):
            y = i * row_h
            bid_int = min(1.0, bid / max_size)
            ask_int = min(1.0, ask / max_size)
            bid_rect = QtCore.QRect(0, y, w // 2, row_h)
            ask_rect = QtCore.QRect(w // 2, y, w // 2, row_h)
            bid_color = QtGui.QColor(18, 216, 250)
            bid_color.setAlphaF(0.1 + 0.9 * bid_int)
            ask_color = QtGui.QColor(255, 95, 86)
            ask_color.setAlphaF(0.1 + 0.9 * ask_int)
            painter.fillRect(bid_rect, bid_color)
            painter.fillRect(ask_rect, ask_color)
        painter.end()
        self.heatmap.setPixmap(pix)
