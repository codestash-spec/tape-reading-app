from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class IBKRHealth:
    last_tick_ts: float = 0.0
    last_dom_ts: float = 0.0
    reconnect_attempts: int = 0

    def record_tick(self) -> None:
        self.last_tick_ts = time.time()

    def record_dom(self) -> None:
        self.last_dom_ts = time.time()

    def is_stale(self, max_age: float = 5.0) -> bool:
        now = time.time()
        return (now - self.last_tick_ts) > max_age and (now - self.last_dom_ts) > max_age
