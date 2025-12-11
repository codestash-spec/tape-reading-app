from __future__ import annotations

from typing import Dict, Any

from PySide6 import QtCore, QtGui, QtWidgets

from ui.event_bridge import EventBridge
from ui import helpers
from ui.themes import brand


class FootprintModel(QtCore.QObject):
    changed = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        # price -> {"buy": x, "sell": y, "delta": x - y, "imbalance": percent}
        self.matrix: Dict[float, Dict[str, float]] = {}

    def update(self, fp: Dict[float, Dict[str, float]]) -> None:
        clean = {}
        for p, vols in fp.items():
            try:
                price = float(p)
                buy = float(vols.get("buy", 0.0))
                sell = float(vols.get("sell", 0.0))
            except Exception:
                continue
            delta = buy - sell
            tot = buy + sell
            imbalance = (max(buy, sell) / tot) if tot else 0.0
            clean[price] = {"buy": buy, "sell": sell, "delta": delta, "imbalance": imbalance}
        self.matrix = clean
        self.changed.emit()


class _FootprintCanvas(QtWidgets.QWidget):
    def __init__(self, model: FootprintModel, parent=None) -> None:
        super().__init__(parent)
        self.model = model
        self.model.changed.connect(self.update)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QtGui.QPainter(self)
        try:
            painter.fillRect(self.rect(), QtGui.QColor(brand.BG_PANEL))
            fp = self.model.matrix
            if not fp:
                return
            prices = sorted(fp.keys(), reverse=True)
            if not prices:
                return
            max_vol = max((max(v["buy"], v["sell"]) for v in fp.values()), default=1.0)
            cell_h = max(12, int(self.height() / len(prices)))
            cell_w = self.width() // 3
            y = 0
            for price in prices:
                vols = fp[price]
                buy = vols["buy"]
                sell = vols["sell"]
                delta = vols["delta"]
                imb = vols["imbalance"]

                buy_int = min(1.0, buy / max_vol)
                sell_int = min(1.0, sell / max_vol)
                delta_color = QtGui.QColor("#12d8fa") if delta >= 0 else QtGui.QColor("#ff5f56")
                delta_color.setAlphaF(0.1 + 0.8 * min(1.0, abs(delta) / max_vol))

                # buy cell
                buy_rect = QtCore.QRect(0, y, cell_w, cell_h - 1)
                buy_color = QtGui.QColor(18, 216, 250)
                buy_color.setAlphaF(0.1 + 0.8 * buy_int)
                painter.fillRect(buy_rect, buy_color)
                painter.setPen(QtGui.QPen(QtGui.QColor(brand.TEXT_LIGHT)))
                painter.drawText(buy_rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, f"{buy:.0f}")

                # sell cell
                sell_rect = QtCore.QRect(cell_w, y, cell_w, cell_h - 1)
                sell_color = QtGui.QColor(255, 95, 86)
                sell_color.setAlphaF(0.1 + 0.8 * sell_int)
                painter.fillRect(sell_rect, sell_color)
                painter.drawText(sell_rect.adjusted(4, 0, -4, 0), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, f"{sell:.0f}")

                # delta/imbalance cell
                delta_rect = QtCore.QRect(cell_w * 2, y, cell_w, cell_h - 1)
                painter.fillRect(delta_rect, delta_color)
                painter.drawText(
                    delta_rect.adjusted(4, 0, -4, 0),
                    QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                    f"{delta:.0f} | {imb*100:.0f}%",
                )

                # price label overlay
                painter.setPen(QtGui.QPen(QtGui.QColor("#b0b8c3")))
                painter.drawText(QtCore.QRect(0, y, self.width(), cell_h), QtCore.Qt.AlignCenter, f"{price:.2f}")

                y += cell_h
        finally:
            painter.end()


class FootprintPanel(QtWidgets.QWidget):
    """
    Footprint with buy/sell, delta e imbalance por nível de preço.
    Throttled updates (~60 FPS) and drag-pause for smoothness.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = FootprintModel()
        self.canvas = _FootprintCanvas(self.model)
        self.canvas.setFont(QtGui.QFont(brand.FONT_FAMILY, brand.FONT_MEDIUM))
        self.canvas.setMinimumHeight(140)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self._pending: Dict[str, Any] | None = None
        self._throttle = QtCore.QTimer(self)
        self._throttle.setInterval(int(1000 / 60))
        self._throttle.timeout.connect(self._flush)
        self._throttle.start()

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.footprintUpdated.connect(self.queue_footprint)
        bridge.microstructureUpdated.connect(self.queue_from_snapshot)

    def queue_footprint(self, fp: Dict[str, Any]) -> None:
        self._pending = fp

    def queue_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        fp = snapshot.get("footprint") or {}
        if fp:
            self._pending = fp

    def _flush(self) -> None:
        if helpers.UI_UPDATE_PAUSED or self._pending is None:
            return
        data = self._pending
        self._pending = None
        self.model.update(data)
