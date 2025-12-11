from __future__ import annotations

from PySide6 import QtWidgets, QtCore, QtGui
from ui.event_bridge import EventBridge
from ui.themes import brand
from ui import helpers


class HeatmapPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ladder = []
        self._pending = None
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(int(1000 / 60))
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("dom_snapshot", self._on_dom)

    def _on_dom(self, evt) -> None:
        payload = evt.payload or {}
        ladder_raw = payload.get("ladder") or payload.get("dom") or payload.get("levels") or []
        self.ladder = []
        if isinstance(ladder_raw, dict):
            for price, entry in ladder_raw.items():
                if isinstance(entry, dict):
                    self.ladder.append((float(price), float(entry.get("bid", 0)), float(entry.get("ask", 0))))
        elif isinstance(ladder_raw, list):
            for level in ladder_raw:
                try:
                    self.ladder.append((float(level.get("price")), float(level.get("bid", 0)), float(level.get("ask", 0))))
                except Exception:
                    continue
        self.ladder = sorted(self.ladder, key=lambda r: r[0], reverse=True)[:80]
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if helpers.UI_UPDATE_PAUSED:
            return
        painter = QtGui.QPainter(self)
        try:
            painter.fillRect(self.rect(), QtGui.QColor(brand.BG_PANEL))
            if not self.ladder:
                return
            w = self.width()
            h = self.height()
            max_size = max(max(b, a) for _, b, a in self.ladder) or 1.0
            row_h = max(2, h // len(self.ladder))
            for i, (price, bid, ask) in enumerate(self.ladder):
                y = i * row_h
                bid_w = int((bid / max_size) * (w / 2))
                ask_w = int((ask / max_size) * (w / 2))
                bid_rect = QtCore.QRect((w // 2) - bid_w, y, bid_w, row_h - 1)
                ask_rect = QtCore.QRect(w // 2, y, ask_w, row_h - 1)
                bid_color = QtGui.QColor(18, 216, 250, int(40 + 180 * (bid / max_size)))
                ask_color = QtGui.QColor(255, 95, 86, int(40 + 180 * (ask / max_size)))
                painter.fillRect(bid_rect, bid_color)
                painter.fillRect(ask_rect, ask_color)
        finally:
            painter.end()
