from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class VolatilityPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Volatility")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("volatility_update", self._on_vol)

    def _on_vol(self, evt):
        self.label.setText(f"ATR={evt.payload.get('atr', 0.0):.2f}")
