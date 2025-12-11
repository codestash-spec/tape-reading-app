from __future__ import annotations

from PySide6 import QtWidgets


class MarketWatchPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.list = QtWidgets.QListWidget()
        for sym in ["BTCUSDT", "ETHUSDT", "XAUUSD", "GC", "NAS100", "SP500"]:
            self.list.addItem(sym)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Market Watch"))
        layout.addWidget(self.list)
        self.setLayout(layout)
