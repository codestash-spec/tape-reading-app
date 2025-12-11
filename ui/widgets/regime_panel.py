from __future__ import annotations

from PySide6 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg

from ui.event_bridge import EventBridge
from ui.themes import brand


class RegimePanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Regime")
        self.history: list[str] = []
        self.timeline = QtWidgets.QListWidget()
        self.timeline.setMaximumHeight(120)
        self.plot = pg.PlotWidget(background=brand.BG_DARK)
        self.plot.setMinimumHeight(60)
        self.curve = self.plot.plot(pen=pg.mkPen("#7cffc4", width=1.5))
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.timeline)
        layout.addWidget(self.plot)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("regime_update", self._on_regime)

    def _on_regime(self, evt):
        regime = str(evt.payload.get("regime"))
        color = {
            "trending": "#12d8fa",
            "ranging": "#7cffc4",
            "squeezing": "#ffaa00",
        }.get(regime, "#b0b8c3")
        self.label.setText(regime)
        self.label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.history.append(regime)
        if len(self.history) > 20:
            self.history.pop(0)
        self.timeline.clear()
        for r in reversed(self.history):
            item = QtWidgets.QListWidgetItem(r)
            item.setForeground(QtGui.QBrush(QtGui.QColor(color)))
            self.timeline.addItem(item)
        self.curve.setData(list(range(len(self.history))), [1 if r == "trending" else 0 if r == "ranging" else -1 for r in self.history])
