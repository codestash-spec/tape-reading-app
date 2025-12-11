from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class AlertsPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.view = QtWidgets.QTextEdit()
        self.view.setReadOnly(True)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.alertReceived.connect(self._on_alert_payload)
        bridge.bus.subscribe("alert_event", self._on_alert_evt)

    def _on_alert_evt(self, evt):
        self._on_alert_payload(evt.payload)

    def _on_alert_payload(self, payload):
        self.view.append(str(payload))
