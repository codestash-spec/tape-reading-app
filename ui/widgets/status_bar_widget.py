from __future__ import annotations

from typing import Dict

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class StatusBarWidget(QtWidgets.QWidget):
    """
    Compact status indicators for connections, risk and mode.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.conn_label = QtWidgets.QLabel("Conn: ?")
        self.risk_label = QtWidgets.QLabel("Risk: ?")
        self.mode_label = QtWidgets.QLabel("Mode: ?")

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.conn_label)
        layout.addWidget(self.risk_label)
        layout.addWidget(self.mode_label)
        layout.addStretch()
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge, mode: str = "sim") -> None:
        self.mode_label.setText(f"Mode: {mode}")
        bridge.orderStatusUpdated.connect(self._on_order)
        bridge.riskStatusUpdated.connect(self._on_risk)

    def _on_order(self, evt: Dict) -> None:
        broker = evt.get("source", "exec")
        self.conn_label.setText(f"Conn: {broker}")

    def _on_risk(self, evt: Dict) -> None:
        status = "OK" if evt.get("approved", True) else "HALT"
        self.risk_label.setText(f"Risk: {status}")

