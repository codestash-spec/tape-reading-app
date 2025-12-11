from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import pyqtgraph as pg
from PySide6 import QtWidgets

from ui.event_bridge import EventBridge
from ui.models import DeltaSeriesModel


class DeltaPanel(QtWidgets.QWidget):
    """
    Displays cumulative delta series using pyqtgraph with zoom/pan.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.model = DeltaSeriesModel()
        self.plot = pg.PlotWidget(background="#0b132b")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.curve = self.plot.plot(pen=pg.mkPen("#14a1ff", width=2))

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.setLayout(layout)

        self.model.changed.connect(self.redraw)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.deltaUpdated.connect(self.update_delta)
        bridge.microstructureUpdated.connect(self.update_from_snapshot)

    def update_delta(self, data: Dict) -> None:
        value = float(data.get("cumulative_delta", data.get("delta", 0.0)) or 0.0)
        self.model.append_delta(datetime.now(timezone.utc), value)

    def update_from_snapshot(self, snapshot: Dict) -> None:
        value = snapshot.get("cumulative_delta") or snapshot.get("delta")
        if value is not None:
            self.update_delta({"cumulative_delta": value})

    def redraw(self) -> None:
        if not self.model.ts:
            return
        self.curve.setData(self.model.ts, self.model.values)
