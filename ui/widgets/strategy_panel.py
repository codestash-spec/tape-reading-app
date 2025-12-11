from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import StrategySignalsModel


class StrategyPanel(QtWidgets.QWidget):
    """
    Displays active signals, playbooks and opportunity meter.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = StrategySignalsModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        self.opportunity = QtWidgets.QProgressBar()
        self.opportunity.setRange(0, 100)
        self.opportunity.setFormat("Opportunity %p%")

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.opportunity)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.signalGenerated.connect(self.append_signal)

    def append_signal(self, sig: Dict) -> None:
        self.model.append_signal(sig)
        score = float(sig.get("score", 0.0))
        self.opportunity.setValue(min(100, int(abs(score) * 100)))
