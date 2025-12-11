from __future__ import annotations

from collections import deque

from PySide6 import QtWidgets

from ui.event_bridge import EventBridge


class LogsPanel(QtWidgets.QWidget):
    """
    Live logs with filtering and bounded buffer.
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

        self._buffer: deque[str] = deque(maxlen=1000)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.logReceived.connect(self.append_log)

    def append_log(self, record: str) -> None:
        self._buffer.append(record)
        if self._matches_filter(record):
            self.view.append(record)

    def _matches_filter(self, line: str) -> bool:
        text = self.search.text()
        if not text:
            return True
        return text.lower() in line.lower()

    def _on_search(self, text: str) -> None:
        self.view.clear()
        for line in self._buffer:
            if self._matches_filter(line):
                self.view.append(line)
