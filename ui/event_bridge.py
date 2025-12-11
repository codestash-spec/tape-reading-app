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

    def stop(self) -> None:
        for et in self._subscriptions:
            self.bus.unsubscribe(et, self._on_event)
        self._subscriptions.clear()
        if self._logger_handler:
            logging.getLogger().removeHandler(self._logger_handler)
            self._logger_handler = None

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {str(k): self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._sanitize(v) for v in obj]
        try:
            import collections

            if isinstance(obj, collections.defaultdict):
                return {str(k): self._sanitize(v) for k, v in obj.items()}
        except Exception:
            pass
        return obj

    def _normalize_dom(self, payload: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        ladder: Dict[str, Dict[str, float]] = {}
        raw = payload.get("ladder") or payload.get("levels") or []
        if "bids" in payload or "asks" in payload:
            for side_key, is_bid in (("bids", True), ("asks", False)):
                for level in payload.get(side_key, []):
                    price = level.get("price")
                    size = level.get("size")
                    if price is None or size is None:
                        continue
                    entry = ladder.setdefault(str(price), {"bid": 0.0, "ask": 0.0})
                    if is_bid:
                        entry["bid"] = float(size)
                    else:
                        entry["ask"] = float(size)
        elif isinstance(raw, dict):
            for price, entry in raw.items():
                if isinstance(entry, dict):
                    ladder[str(price)] = {
                        "bid": float(entry.get("bid", 0.0) or 0.0),
                        "ask": float(entry.get("ask", 0.0) or 0.0),
                    }
        elif isinstance(raw, list):
            for level in raw:
                if isinstance(level, dict):
                    price = level.get("price")
                    if price is None:
                        continue
                    ladder[str(price)] = {
                        "bid": float(level.get("bid", 0.0) or 0.0),
                        "ask": float(level.get("ask", 0.0) or 0.0),
                    }
                elif isinstance(level, (list, tuple)) and len(level) >= 3:
                    ladder[str(level[0])] = {"bid": float(level[1] or 0.0), "ask": float(level[2] or 0.0)}
        return ladder

    def _on_event(self, evt: MarketEvent) -> None:
        et = evt.event_type
        payload = self._sanitize(evt.payload or {})
        if et == "dom_snapshot":
            payload["ladder"] = self._normalize_dom(payload)
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
