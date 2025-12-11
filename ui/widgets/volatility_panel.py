from __future__ import annotations

from PySide6 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

from ui.event_bridge import EventBridge
from ui.themes import brand


class VolatilityPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.atr_short = 0.0
        self.atr_long = 0.0
        self.label = QtWidgets.QLabel("ATR")
        self.bar_short = QtWidgets.QProgressBar()
        self.bar_long = QtWidgets.QProgressBar()
        for bar in (self.bar_short, self.bar_long):
            bar.setRange(0, 1000)
            bar.setTextVisible(True)
        self.history = []
        self.plot = pg.PlotWidget(background=brand.BG_DARK)
        self.plot.setMinimumHeight(80)
        self.curve = self.plot.plot(pen=pg.mkPen(brand.ACCENT, width=1.5))
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(QtWidgets.QLabel("ATR(14)"))
        layout.addWidget(self.bar_short)
        layout.addWidget(QtWidgets.QLabel("ATR(100)"))
        layout.addWidget(self.bar_long)
        layout.addWidget(self.plot)
        layout.addStretch()
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("volatility_update", self._on_vol)

    def _on_vol(self, evt):
        self.atr_short = float(evt.payload.get("atr_short", evt.payload.get("atr", 0.0)) or 0.0)
        self.atr_long = float(evt.payload.get("atr_long", self.atr_short) or 0.0)
        self.label.setText(f"ATR(14)={self.atr_short:.2f}  ATR(100)={self.atr_long:.2f}")
        self.bar_short.setValue(int(self.atr_short * 10))
        self.bar_long.setValue(int(self.atr_long * 10))
        self.history.append(self.atr_short)
        if len(self.history) > 300:
            self.history.pop(0)
        xs = list(range(len(self.history)))
        self.curve.setData(xs, self.history)
