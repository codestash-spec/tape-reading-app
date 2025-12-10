from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import ExecutionOrdersModel


class ExecutionPanel(QtWidgets.QWidget):
    """
    Shows active orders/fills with optional manual actions (stubbed).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = ExecutionOrdersModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)

        self.cancel_btn = QtWidgets.QPushButton("Cancel Selected")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.cancel_btn)
        self.setLayout(layout)

        self._cancel_callback = None

    def connect_bridge(self, bridge: EventBridge, on_cancel=None) -> None:
        bridge.orderStatusUpdated.connect(self.update_order)
        self._cancel_callback = on_cancel

    def update_order(self, evt: Dict) -> None:
        self.model.upsert_order(evt)

    def _on_cancel_clicked(self) -> None:
        if not self._cancel_callback:
            return
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        order_id = self.model.rows[idx.row()][0]
        self._cancel_callback(order_id)

