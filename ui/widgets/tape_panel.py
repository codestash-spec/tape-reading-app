from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import TapeTableModel


class TapePanel(QtWidgets.QWidget):
    """
    Time & Sales view.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = TapeTableModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.tapeUpdated.connect(self.append_trade)

    def append_trade(self, trade: Dict) -> None:
        self.model.append_trade(trade)

