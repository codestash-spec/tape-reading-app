from __future__ import annotations

from typing import Callable, Dict, Optional

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import ExecutionOrdersModel


class ExecutionPanel(QtWidgets.QWidget):
    """
    Shows active orders/fills with manual actions and smart router hints.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = ExecutionOrdersModel()
        self.view = QtWidgets.QTableView()
        self.view.setModel(self.model)
        self.view.verticalHeader().setVisible(False)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setAlternatingRowColors(True)

        self.cancel_btn = QtWidgets.QPushButton("Cancel Selected")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)

        self.router_label = QtWidgets.QLabel("Router: smart")
        self.queue_label = QtWidgets.QLabel("Queue ETA: —")
        self.slippage_label = QtWidgets.QLabel("Slippage tol: —")

        info_layout = QtWidgets.QHBoxLayout()
        info_layout.addWidget(self.router_label)
        info_layout.addWidget(self.queue_label)
        info_layout.addWidget(self.slippage_label)
        info_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(info_layout)
        layout.addWidget(self.view)
        layout.addWidget(self.cancel_btn)
        self.setLayout(layout)

        self._cancel_callback: Optional[Callable[[str], None]] = None

    def connect_bridge(self, bridge: EventBridge, on_cancel: Optional[Callable[[str], None]] = None) -> None:
        bridge.orderStatusUpdated.connect(self.update_order)
        self._cancel_callback = on_cancel

    def update_order(self, evt: Dict) -> None:
        self.model.upsert_order(evt)
        eta = evt.get("metadata", {}).get("eta_sec") if isinstance(evt.get("metadata"), dict) else None
        if eta:
            self.queue_label.setText(f"Queue ETA: {eta}s")
        slip = evt.get("slippage_bps")
        if slip is not None:
            self.slippage_label.setText(f"Slippage tol: {float(slip):.2f}bps")

    def _on_cancel_clicked(self) -> None:
        if not self._cancel_callback:
            return
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        order_id = self.model.rows[idx.row()][0]
        self._cancel_callback(order_id)
