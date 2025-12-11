from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class VolumeProfilePanel(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Volume Profile")
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.bus.subscribe("volume_profile_update", self._on_profile)

    def _on_profile(self, evt):
        self.label.setText(f"POC={evt.payload.get('poc')}")
