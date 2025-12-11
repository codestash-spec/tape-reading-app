from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class RegimePanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Regime")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("regime_update", self._on_regime)

    def _on_regime(self, evt):
        self.label.setText(str(evt.payload.get("regime")))
