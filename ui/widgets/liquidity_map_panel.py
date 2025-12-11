from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class LiquidityMapPanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Liquidity Map")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("liquidity_update", self._on_liq)

    def _on_liq(self, evt):
        self.label.setText(f"Liquidity levels={len(evt.payload.get('resting', {}))}")
