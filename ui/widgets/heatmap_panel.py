from __future__ import annotations

from PySide6 import QtWidgets


class HeatmapPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Heatmap (DOM)")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
