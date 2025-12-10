from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger(__name__)


class KillSwitch:
    """
    Simple kill switch that notifies listeners when engaged.
    """

    def __init__(self) -> None:
        self.engaged = False
        self._listeners: list[Callable[[], None]] = []

    def register(self, fn: Callable[[], None]) -> None:
        self._listeners.append(fn)

    def engage(self) -> None:
        if self.engaged:
            return
        self.engaged = True
        log.error("[RISK] Kill-switch engaged, notifying listeners.")
        for fn in self._listeners:
            try:
                fn()
            except Exception:  # pragma: no cover - defensive
                log.exception("Kill-switch listener error")

    def reset(self) -> None:
        self.engaged = False
