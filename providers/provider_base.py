from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from typing import Any

from models.market_event import MarketEvent
from core.event_bus import EventBus


class ProviderBase(ABC):
    """
    Abstract provider: normalizes raw feed into MarketEvents and publishes to EventBus.
    """

    def __init__(self, event_bus: EventBus, settings: dict[str, Any], symbol: str) -> None:
        self.bus = event_bus
        self.settings = settings or {}
        self.symbol = symbol
        self._thread: threading.Thread | None = None
        self._running = False

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    @abstractmethod
    def subscribe_dom(self) -> None:
        ...

    @abstractmethod
    def subscribe_trades(self) -> None:
        ...

    @abstractmethod
    def subscribe_quotes(self) -> None:
        ...

    @abstractmethod
    def normalize_dom(self, raw: Any) -> MarketEvent:
        ...

    @abstractmethod
    def normalize_trade(self, raw: Any) -> MarketEvent:
        ...

    # utilities for synthetic providers
    def _start_thread(self, target) -> None:
        self._running = True
        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def _stop_thread(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
