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
        bridge.bus.subscribe("alert_event", self._on_alert)

    def _on_alert(self, evt):
        self.view.append(str(evt.payload))
