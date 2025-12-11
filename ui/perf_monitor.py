from __future__ import annotations

import time
from collections import deque

from PySide6 import QtCore, QtWidgets


class FPSMonitor(QtWidgets.QLabel):
    """
    Simple FPS monitor that can be tick()'d from the UI loop.
    """

    def __init__(self, window: QtWidgets.QWidget, interval_ms: int = 1000) -> None:
        super().__init__(window)
        self.samples = deque(maxlen=200)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._update)
        self.timer.start()
        self.setStyleSheet("color: #e0e6ed;")
        self.setText("FPS: --")
        self._last = time.time()

    def tick(self) -> None:
        now = time.time()
        dt = now - self._last
        self._last = now
        if dt > 0:
            self.samples.append(1.0 / dt)

    def _update(self) -> None:
        if not self.samples:
            return
        fps = sum(self.samples) / len(self.samples)
        self.setText(f"FPS: {fps:.1f}")
