from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class LogsPanel(QtWidgets.QWidget):
    """
    Live log stream with basic filtering.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.view = QtWidgets.QTextEdit()
        self.view.setReadOnly(True)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.logReceived.connect(self.append_log)

    def append_log(self, record: str) -> None:
        self.view.append(record)

