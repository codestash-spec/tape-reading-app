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
                self._subscribers[event_type].append(callback)
            else:
                for et in event_type:
                    self._subscribers[et].append(callback)

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
