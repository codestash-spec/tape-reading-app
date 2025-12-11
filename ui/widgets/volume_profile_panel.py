from __future__ import annotations

from PySide6 import QtWidgets, QtGui, QtCore
from ui import helpers
from ui.themes import brand
from ui.event_bridge import EventBridge
from ui.state import UIState


class VolumeProfilePanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.profile = {}
        self.poc = None
        self.value_area = []
        self.setMinimumHeight(120)
        self._pending = None
        self._throttle = QtCore.QTimer(self)
        self._throttle.setInterval(int(1000 / 60))
        self._throttle.timeout.connect(self.update)
        self._throttle.start()

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("volume_profile_update", self._on_profile)

    def _on_profile(self, evt):
        self._pending = evt.payload
        self.profile = evt.payload.get("histogram", {})
        self.poc = evt.payload.get("poc")
        self.value_area = evt.payload.get("value_area", [])
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if UIState.is_paused():
            return
        if not self.profile:
            return
        painter = QtGui.QPainter(self)
        try:
            painter.fillRect(self.rect(), QtGui.QColor("#0f1b2b"))
            w = self.width()
            h = self.height()
            max_vol = max(self.profile.values()) if self.profile else 1.0
            sorted_prices = sorted(self.profile.keys())
            bar_h = max(4, h // max(1, len(sorted_prices)))
            y = h
            for price in reversed(sorted_prices):
                vol = self.profile[price]
                width = int((vol / max_vol) * (w * 0.9))
                rect = QtCore.QRect(0, y - bar_h, width, bar_h - 1)
                grad = QtGui.QLinearGradient(rect.topLeft(), rect.topRight())
                grad.setColorAt(0, QtGui.QColor("#0a3a53"))
                grad.setColorAt(1, QtGui.QColor(18, 216, 250))
                painter.fillRect(rect, grad)
                # Value Area shading
                if price in self.value_area:
                    va_color = QtGui.QColor("#7cffc4")
                    va_color.setAlphaF(0.25)
                    painter.fillRect(rect, va_color)
                # POC line
                if price == self.poc:
                    painter.setPen(QtGui.QPen(QtGui.QColor("#ffd700"), 2))
                    painter.drawLine(rect.right(), y - bar_h, rect.right(), y)
                # Price labels on left margin
                painter.setPen(QtGui.QPen(QtGui.QColor("#8aa0b4")))
                painter.drawText(QtCore.QRect(0, y - bar_h, w, bar_h), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, f"{price:.2f}")
                y -= bar_h
        finally:
            painter.end()
        helpers.fps_tick()
