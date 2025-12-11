from __future__ import annotations

from collections import deque
from typing import Any

from PySide6 import QtWidgets, QtCore

from ui.event_bridge import EventBridge
from ui import helpers


class ProviderDebugPanel(QtWidgets.QWidget):
    """
    Displays recent provider events (sampled) with latency estimation.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.list = QtWidgets.QListWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)
        self.setLayout(layout)
        self.buffer = deque(maxlen=200)

    def connect_bridge(self, bridge: EventBridge) -> None:
        for et in ["trade", "dom_snapshot", "quote", "order_event", "signal"]:
            bridge.bus.subscribe(et, self._on_evt)

    def _on_evt(self, evt: Any) -> None:
        if helpers.UI_UPDATE_PAUSED:
            return
        ts = getattr(evt, "timestamp", None)
        delay = ""
        if ts:
            delay = f" lag={(QtCore.QDateTime.currentDateTimeUtc().toSecsSinceEpoch() - int(ts.timestamp())):d}s"
        summary = f"{getattr(evt, 'event_type', '?')} {getattr(evt, 'source', '?')} {getattr(evt, 'symbol', '')}{delay}"
        self.buffer.appendleft(summary)
        self.list.clear()
        for item in list(self.buffer):
            self.list.addItem(item)
