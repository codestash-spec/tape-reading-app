import threading
import queue
import traceback
from typing import Callable, Dict, List, Any


class Event:
    """
    Base event class.
    Every event must contain:
        - type: str  -> used for routing
        - payload: dict or any
    """
    def __init__(self, event_type: str, payload: Any):
        self.type = event_type
        self.payload = payload


class EventBus:
    """
    High-performance event bus for institutional-grade apps.
    
    Features:
    - Thread-safe publish/subscribe
    - Internal queue (non-blocking)
    - Worker thread dispatch loop
    - Per-event-type subscriptions
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.queue = queue.Queue()
        self.running = True

        self.worker = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.worker.start()

    # --------------------------------------------------------
    # SUBSCRIBE
    # --------------------------------------------------------
    def subscribe(self, event_type: str, callback: Callable):
        """
        Register a callback for a specific event type.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    # --------------------------------------------------------
    # PUBLISH
    # --------------------------------------------------------
    def publish(self, event: Event):
        """
        Add an event to the queue.
        Non-blocking.
        """
        self.queue.put(event)

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------
    def _dispatch_loop(self):
        """
        Internal worker thread that processes events.
        """
        while self.running:
            try:
                event = self.queue.get()
                if event is None:
                    continue

                # No subscribers for this event type
                if event.type not in self.subscribers:
                    continue

                # Dispatch to all subscribers
                for callback in self.subscribers[event.type]:
                    try:
                        callback(event)
                    except Exception:
                        # We NEVER allow a callback failure to kill the bus
                        print("[EventBus] Error in callback:")
                        traceback.print_exc()

            except Exception:
                print("[EventBus] Fatal error in dispatch loop:")
                traceback.print_exc()

    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------
    def stop(self):
        """
        Stop the event bus safely.
        """
        self.running = False
        self.queue.put(None)
        self.worker.join()
