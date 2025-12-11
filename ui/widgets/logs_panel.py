from __future__ import annotations

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class LogsPanel(QtWidgets.QWidget):
    """
    Live log stream with filtering and search.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.view = QtWidgets.QTextEdit()
        self.view.setReadOnly(True)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search logs...")
        self.search.textChanged.connect(self._on_search)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.search)
        layout.addWidget(self.view)
        self.setLayout(layout)

        self._buffer: list[str] = []

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.logReceived.connect(self.append_log)

    def append_log(self, record: str) -> None:
        self._buffer.append(record)
        self.view.append(record)

    def _on_search(self, text: str) -> None:
        self.view.clear()
        for line in self._buffer:
            if text.lower() in line.lower():
                self.view.append(line)
