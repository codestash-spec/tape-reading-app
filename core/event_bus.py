from __future__ import annotations

import logging
import queue
import threading
from collections import defaultdict
from typing import Callable, DefaultDict, Dict, Iterable, List, Optional

from models.market_event import MarketEvent

Callback = Callable[[MarketEvent], None]


class EventBus:
    """
    Thread-safe event bus with a single dispatch worker.

    - Non-blocking publish (queue-backed)
    - Per-event-type subscription with optional wildcard "*"
    - Safe shutdown that drains the queue
    """

    def __init__(self, queue_maxsize: int = 0) -> None:
        self._subscribers: DefaultDict[str, List[Callback]] = defaultdict(list)
        self._queue: queue.Queue[Optional[MarketEvent]] = queue.Queue(maxsize=queue_maxsize)
        self._lock = threading.RLock()
        self._running = threading.Event()
        self._running.set()
        self.allowed_sources: set[str] | None = None

        self._worker = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._worker.start()

    # --------------------------------------------------------
    # SUBSCRIBE
    # --------------------------------------------------------
    def subscribe(self, event_type: str | Iterable[str], callback: Callback) -> None:
        """
        Register a callback for one or more event types.
        Supports "*" wildcard for all events.
        """
        with self._lock:
            if isinstance(event_type, str):
                if callback in self._subscribers[event_type]:
                    logging.getLogger(__name__).warning("[EventBus] duplicate callback detected for %s", event_type)
                self._subscribers[event_type].append(callback)
            else:
                for et in event_type:
                    if callback in self._subscribers[et]:
                        logging.getLogger(__name__).warning("[EventBus] duplicate callback detected for %s", et)
                    self._subscribers[et].append(callback)

    def unsubscribe(self, event_type: str | Iterable[str], callback: Callback) -> None:
        """
        Remove a callback from one or more event types.
        """
        with self._lock:
            types = [event_type] if isinstance(event_type, str) else list(event_type)
            for et in types:
                if et in self._subscribers and callback in self._subscribers[et]:
                    self._subscribers[et].remove(callback)

    def unsubscribe_all_for(self, callback: Callback) -> None:
        """
        Remove a callback from every event type where it is registered.
        """
        with self._lock:
            for et, subs in list(self._subscribers.items()):
                if callback in subs:
                    subs[:] = [cb for cb in subs if cb is not callback]

    # --------------------------------------------------------
    # PUBLISH
    # --------------------------------------------------------
    def publish(self, event: MarketEvent) -> None:
        """
        Add an event to the queue (non-blocking).
        """
        if not self._running.is_set():
            logging.getLogger(__name__).warning("EventBus.publish called after stop(). Event dropped.")
            return
        if self.allowed_sources is not None:
            src = getattr(event, "source", None)
            src_key = str(src).lower() if src is not None else ""
            allowed = {s.lower() for s in self.allowed_sources}
            # Allow internal engines to bypass provider filter
            internal_sources = {
                "",
                "microstructure",
                "liquidity",
                "liquidity_map",
                "liquidity_map_engine",
                "volume_profile",
                "volume_profile_engine",
                "volatility",
                "regime",
                "regime_engine",
                "strategy",
                "strategy_orchestrator",
                "execution",
                "router",
                "risk",
                "ui",
                "tape",
                "delta",
                "footprint",
                "sim",
                "ohlc_engine",
                "spoof_detector",
                "iceberg_detector",
                "large_trade_detector",
                "simple_strategy",
            }
            if src_key not in allowed and src_key not in internal_sources:
                logging.getLogger(__name__).error(
                    "[Error][GhostEvent] Event received from provider that should be DEAD source=%s allowed=%s",
                    src,
                    self.allowed_sources,
                )
                return
        self._queue.put_nowait(event)

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------
    def _dispatch_loop(self) -> None:
        """
        Internal worker thread that processes events.
        """
        log = logging.getLogger(__name__)

        while self._running.is_set() or not self._queue.empty():
            try:
                event = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if event is None:
                continue

            event_type = getattr(event, "event_type", None) or getattr(event, "type", None)
            if not event_type:
                log.error("Discarding event without type: %s", event)
                continue

            with self._lock:
                callbacks = list(self._subscribers.get(event_type, [])) + list(self._subscribers.get("*", []))

            if not callbacks:
                continue

            for callback in callbacks:
                try:
                    callback(event)
                except Exception:
                    log.exception("Error in callback for event_type=%s", event_type)

    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------
    def stop(self, timeout: float = 1.0) -> None:
        """
        Stop the event bus safely and wait for the worker to drain.
        """
        if not self._running.is_set():
            return

        self._running.clear()
        self._queue.put(None)
        self._worker.join(timeout=timeout)

    def count_subscribers(self) -> int:
        with self._lock:
            return sum(len(v) for v in self._subscribers.values())
