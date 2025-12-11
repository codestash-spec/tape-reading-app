from __future__ import annotations

from collections import deque
from typing import Deque, Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import TapeTableModel
from ui.themes import brand


class TapePanel(QtWidgets.QWidget):
    """
    Time & Sales view with speed meter.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = TapeTableModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)

        self.speed_bar = QtWidgets.QProgressBar()
        self.speed_bar.setRange(0, 100)
        self.speed_bar.setFormat("Tape Speed %p%")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.speed_bar)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self._last_trades: Deque[float] = deque(maxlen=50)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.tapeUpdated.connect(self.append_trade)

    def append_trade(self, trade: Dict) -> None:
        self.model.append_trade(trade)
        self._last_trades.append(trade.get("size", 0))
        if self._last_trades:
            avg_speed = sum(self._last_trades) / len(self._last_trades)
            val = min(100, int(avg_speed))
            self.speed_bar.setValue(val)
