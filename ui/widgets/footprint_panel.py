from __future__ import annotations

from typing import Dict

from PySide6 import QtCore, QtGui, QtWidgets

from ui.event_bridge import EventBridge
from ui.models import FootprintModel
from ui.themes import brand


class _FootprintCanvas(QtWidgets.QWidget):
    def __init__(self, model: FootprintModel, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.model.changed.connect(self.update)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(brand.BG_PANEL))
        fp = self.model.matrix
        if not fp:
            painter.end()
            return
        prices = sorted(fp.keys(), reverse=True)
        if not prices:
            painter.end()
            return
        max_vol = max((max(v.get("buy", 0.0), v.get("sell", 0.0)) for v in fp.values()), default=1.0)
        cell_h = max(14, int(self.height() / len(prices)))
        cell_w = self.width() // 2
        y = 0
        for price in prices:
            vols = fp[price]
            buy = vols.get("buy", 0.0)
            sell = vols.get("sell", 0.0)
            buy_intensity = min(1.0, buy / max_vol)
            sell_intensity = min(1.0, sell / max_vol)

            buy_rect = QtCore.QRect(0, y, cell_w, cell_h - 1)
            sell_rect = QtCore.QRect(cell_w, y, cell_w, cell_h - 1)
            buy_color = QtGui.QColor(18, 216, 250)
            buy_color.setAlphaF(0.1 + 0.8 * buy_intensity)
            sell_color = QtGui.QColor(255, 95, 86)
            sell_color.setAlphaF(0.1 + 0.8 * sell_intensity)

            painter.fillRect(buy_rect, buy_color)
            painter.fillRect(sell_rect, sell_color)

            painter.setPen(QtGui.QPen(QtGui.QColor(brand.TEXT_LIGHT)))
            painter.drawText(buy_rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, f"{buy:.0f}")
            painter.drawText(sell_rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, f"{sell:.0f}")
            painter.drawText(QtCore.QRect(0, y, self.width(), cell_h), QtCore.Qt.AlignCenter, f"{price:.2f}")

            y += cell_h


class FootprintPanel(QtWidgets.QWidget):
    """
    Heatmap footprint with imbalance highlight and tooltips.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = FootprintModel()
        self.canvas = _FootprintCanvas(self.model)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.footprintUpdated.connect(self.update_footprint)
        bridge.microstructureUpdated.connect(self.update_from_snapshot)

    def update_footprint(self, footprint: Dict) -> None:
        self.model.update_footprint(footprint)

    def update_from_snapshot(self, snapshot: Dict) -> None:
        fp = snapshot.get("footprint") or {}
        if fp:
            clean = {}
            for price, vols in fp.items():
                try:
                    price_f = float(price)
                    buy = float(vols.get("buy", 0.0))
                    sell = float(vols.get("sell", 0.0))
                except Exception:
                    continue
                clean[price_f] = {"buy": buy, "sell": sell}
            self.update_footprint(clean)
