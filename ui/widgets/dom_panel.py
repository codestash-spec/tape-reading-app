from __future__ import annotations

from typing import Dict, List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets

from ui.event_bridge import EventBridge
from ui.models import DomTableModel
from ui.themes import brand


class _DomDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, model: DomTableModel, parent=None) -> None:
        super().__init__(parent)
        self.model = model

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:  # type: ignore[override]
        col = index.column()
        row_data = self.model.rows[index.row()]
        painter.save()
        value = row_data[col]
        rect = option.rect

        if col == 1 or col == 2:  # bid/ask size heatmap
            size_val = float(value)
            max_size = max(1.0, max(float(r[col]) for r in self.model.rows))
            intensity = min(1.0, size_val / max_size)
            color = QtGui.QColor(brand.HEATMAP_HIGH if col == 1 else brand.WARNING)
            color.setAlphaF(0.15 + 0.75 * intensity)
            painter.fillRect(rect, color)

            price = float(row_data[0])
            prev = self.model.prev.get(price)
            if prev:
                prev_size = prev[0] if col == 1 else prev[1]
                if size_val > prev_size:
                    painter.fillRect(rect.adjusted(0, 0, -1, -1), QtGui.QColor(0, 200, 120, 60))
                elif size_val < prev_size:
                    painter.fillRect(rect.adjusted(0, 0, -1, -1), QtGui.QColor(200, 80, 80, 60))

        painter.setPen(QtGui.QPen(QtGui.QColor(brand.TEXT_LIGHT)))
        painter.drawText(rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, f"{value}")
        painter.restore()

    def sizeHint(self, option, index):  # type: ignore[override]
        hint = super().sizeHint(option, index)
        hint.setHeight(24)
        return hint


class DomPanel(QtWidgets.QWidget):
    """
    Displays DOM ladder with liquidity heatmap and stacking/pulling highlights.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = DomTableModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.setItemDelegate(_DomDelegate(self.model, self.view))
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

    def update_dom(self, payload: Dict) -> None:
        ladder = payload.get("ladder") or payload.get("levels") or {}
        rows: List[Tuple[float, float, float, float]] = []
        if isinstance(ladder, dict):
            for price_str, sizes in ladder.items():
                try:
                    price = float(price_str)
                except Exception:
                    continue
                bid_val = sizes.get("bid", 0.0) if isinstance(sizes, dict) else sizes or 0.0
                ask_val = sizes.get("ask", 0.0) if isinstance(sizes, dict) else 0.0
                liq_val = sizes.get("liquidity", 0.0) if isinstance(sizes, dict) else 0.0
                try:
                    bid = float(bid_val)
                    ask = float(ask_val)
                    liq = float(liq_val)
                except Exception:
                    continue
                rows.append((price, bid, ask, liq))
        elif isinstance(ladder, list):
            for level in ladder:
                try:
                    price = float(level.get("price", 0.0))
                    bid = float(level.get("bid", 0.0))
                    ask = float(level.get("ask", 0.0))
                    liq = float(level.get("liquidity", 0.0))
                except Exception:
                    continue
                rows.append((price, bid, ask, liq))
        rows = sorted(rows, key=lambda r: r[0], reverse=True)[:200]
        self.model.update_from_dom(rows)
