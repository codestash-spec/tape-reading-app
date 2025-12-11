from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Tuple

import pyqtgraph as pg
from PySide6 import QtWidgets, QtCore

from ui.event_bridge import EventBridge
from ui.themes import brand


class DeltaPanel(QtWidgets.QWidget):
    """
    Institutional delta view with stream + cumulative modes and divergence markers.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.stream: Deque[Tuple[float, float]] = deque(maxlen=2000)
        self.cvd: Deque[Tuple[float, float]] = deque(maxlen=2000)
        self.price: Deque[Tuple[float, float]] = deque(maxlen=2000)
        self.mode_cvd = True

        self.plot = pg.PlotWidget(background=brand.BG_DARK)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.curve_stream = self.plot.plot(pen=pg.mkPen(brand.ACCENT, width=1.5))
        self.curve_cvd = self.plot.plot(pen=pg.mkPen("#7cffc4", width=2))
        self.divergence_scatter = pg.ScatterPlotItem(size=8, brush=pg.mkBrush("#ff5f56"))
        self.plot.addItem(self.divergence_scatter)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.setLayout(layout)

    def connect_bridge(self, bridge: EventBridge) -> None:
        bridge.deltaUpdated.connect(self.update_delta)
        bridge.microstructureUpdated.connect(self.update_from_snapshot)

    def update_delta(self, data: Dict) -> None:
        now_ts = datetime.now(timezone.utc).timestamp()
        try:
            delta_val = float(data.get("delta", data.get("cumulative_delta", 0.0)) or 0.0)
        except Exception:
            delta_val = 0.0
        self.stream.append((now_ts, delta_val))
        last_cvd = self.cvd[-1][1] if self.cvd else 0.0
        self.cvd.append((now_ts, last_cvd + delta_val))
        self._redraw()

    def update_from_snapshot(self, snapshot: Dict) -> None:
        now_ts = datetime.now(timezone.utc).timestamp()
        if "cumulative_delta" in snapshot:
            try:
                cvd_val = float(snapshot.get("cumulative_delta", 0.0))
            except Exception:
                cvd_val = 0.0
            self.cvd.append((now_ts, cvd_val))
        if "price" in snapshot or "mid" in snapshot:
            try:
                price = float(snapshot.get("mid") or snapshot.get("price"))
                self.price.append((now_ts, price))
            except Exception:
                pass
        self._redraw()

    def _detect_divergences(self) -> List[dict]:
        points = []
        if len(self.cvd) < 5 or len(self.price) < 5:
            return points
        # simple check: last cvd slope vs price slope
        cvd_slope = self.cvd[-1][1] - self.cvd[-5][1]
        price_slope = self.price[-1][1] - self.price[-5][1]
        if cvd_slope * price_slope < 0:  # opposite directions
            points.append({"pos": self.stream[-1], "brush": pg.mkBrush("#ffb02e")})
        return points

    def _redraw(self) -> None:
        if self.stream:
            xs, ys = zip(*self.stream)
            self.curve_stream.setData(xs, ys)
        if self.cvd and self.mode_cvd:
            xs, ys = zip(*self.cvd)
            self.curve_cvd.setData(xs, ys)
        else:
            self.curve_cvd.setData([], [])
        self.divergence_scatter.setData(self._detect_divergences())
