from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

from PySide6 import QtCore

from core.event_bus import EventBus
from models.market_event import MarketEvent


class _LogToSignalHandler(logging.Handler):
    def __init__(self, signal: QtCore.SignalInstance) -> None:
        super().__init__()
        self.signal = signal

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.signal.emit(self.format(record))
        except Exception:
            pass


class EventBridge(QtCore.QObject):
    """
    Bridges EventBus events into Qt signals so that widgets update in the UI thread.
    """

    domUpdated = QtCore.Signal(dict)
    deltaUpdated = QtCore.Signal(dict)
    footprintUpdated = QtCore.Signal(dict)
    tapeUpdated = QtCore.Signal(dict)
    microstructureUpdated = QtCore.Signal(dict)
    signalGenerated = QtCore.Signal(dict)
    orderStatusUpdated = QtCore.Signal(dict)
    riskStatusUpdated = QtCore.Signal(dict)
    metricsUpdated = QtCore.Signal(dict)
    logReceived = QtCore.Signal(str)

    def __init__(self, bus: EventBus, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.bus = bus
        self._subscriptions: List[str] = []
        self._logger_handler: Optional[_LogToSignalHandler] = None

    def start(self, event_types: Optional[Iterable[str]] = None) -> None:
        types = event_types or [
            "dom_snapshot",
            "dom_delta",
            "trade",
            "microstructure",
            "signal",
            "order_event",
            "risk_decision",
            "metrics",
            "log",
        ]
        for et in types:
            self.bus.subscribe(et, self._on_event)
            self._subscriptions.append(et)
        self._attach_logging()

    def _on_event(self, evt: MarketEvent) -> None:
        et = evt.event_type
        payload = evt.payload or {}
        if et == "dom_snapshot":
            self.domUpdated.emit(payload)
        elif et == "dom_delta":
            self.domUpdated.emit(payload)
        elif et == "trade":
            self.tapeUpdated.emit(payload)
        elif et == "microstructure":
            snap = payload.get("snapshot", payload)
            self.microstructureUpdated.emit(snap)
            fp = snap.get("footprint")
            if fp:
                self.footprintUpdated.emit(fp)
            features = snap.get("features")
            if features:
                self.deltaUpdated.emit(features)
        elif et == "signal":
            self.signalGenerated.emit(payload)
        elif et == "order_event":
            self.orderStatusUpdated.emit(payload)
        elif et == "risk_decision":
            self.riskStatusUpdated.emit(payload)
        elif et == "metrics":
            self.metricsUpdated.emit(payload)

    def _attach_logging(self) -> None:
        if self._logger_handler:
            return
        handler = _LogToSignalHandler(self.logReceived)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        self._logger_handler = handler

    def stop(self) -> None:
        if self._logger_handler:
            logging.getLogger().removeHandler(self._logger_handler)
            self._logger_handler = None
