from __future__ import annotations

from PySide6 import QtWidgets, QtGui, QtCore
from ui import helpers
from ui.themes import brand
from ui.event_bridge import EventBridge
from ui.state import UIState


class LiquidityMapPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.resting = {}
        self.prev_resting = {}
        self.setMinimumHeight(120)
        self._pending = None
        self._max_history = 50
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(int(1000 / 60))
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("liquidity_update", self._on_liq)

    def _on_liq(self, evt):
        self._pending = evt.payload
        self.prev_resting = self.resting
        self.resting = evt.payload.get("resting", {})
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if UIState.is_paused():
            return
        if not self.resting:
            return
        painter = QtGui.QPainter(self)
        try:
            painter.fillRect(self.rect(), QtGui.QColor("#0f1b2b"))
            w = self.width()
            h = self.height()
            prices = sorted(self.resting.keys(), reverse=True)
            bar_h = max(4, h // max(1, len(prices)))
            max_liq = max(max(v.get("bid", 0.0), v.get("ask", 0.0)) for v in self.resting.values()) or 1.0
            y = 0
            for p in prices:
                entry = self.resting[p]
                bid = entry.get("bid", 0.0)
                ask = entry.get("ask", 0.0)
                bid_w = int((bid / max_liq) * (w / 2))
                ask_w = int((ask / max_liq) * (w / 2))
                # bid gradient
                bid_rect = QtCore.QRect((w // 2) - bid_w, y, bid_w, bar_h - 1)
                bid_grad = QtGui.QLinearGradient(bid_rect.topLeft(), bid_rect.topRight())
                bid_grad.setColorAt(0, QtGui.QColor("#0a3a53"))
                bid_grad.setColorAt(1, QtGui.QColor(18, 216, 250))
                painter.fillRect(bid_rect, bid_grad)
                # ask gradient
                ask_rect = QtCore.QRect(w // 2, y, ask_w, bar_h - 1)
                ask_grad = QtGui.QLinearGradient(ask_rect.topLeft(), ask_rect.topRight())
                ask_grad.setColorAt(0, QtGui.QColor(255, 95, 86))
                ask_grad.setColorAt(1, QtGui.QColor("#5a1a1a"))
                painter.fillRect(ask_rect, ask_grad)
                # change overlay vs previous snapshot (intense zones)
                prev = self.prev_resting.get(p, {})
                d_bid = bid - prev.get("bid", 0.0)
                d_ask = ask - prev.get("ask", 0.0)
                if abs(d_bid) > 0:
                    delta_color = QtGui.QColor("#12d8fa") if d_bid > 0 else QtGui.QColor("#0a3a53")
                    delta_color.setAlphaF(min(0.9, 0.2 + 0.8 * abs(d_bid) / max_liq))
                    painter.fillRect(bid_rect, delta_color)
                if abs(d_ask) > 0:
                    delta_color = QtGui.QColor("#ff5f56") if d_ask > 0 else QtGui.QColor("#5a1a1a")
                    delta_color.setAlphaF(min(0.9, 0.2 + 0.8 * abs(d_ask) / max_liq))
                    painter.fillRect(ask_rect, delta_color)
                # label
                painter.setPen(QtGui.QPen(QtGui.QColor("#8aa0b4")))
                painter.drawText(0, y, w, bar_h, QtCore.Qt.AlignCenter, f"{p}")
                y += bar_h
        finally:
            painter.end()
        helpers.fps_tick()
