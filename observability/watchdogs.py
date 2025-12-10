from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict


class Watchdogs:
    def __init__(self, max_stale_seconds: int = 5) -> None:
        self.max_stale = timedelta(seconds=max_stale_seconds)
        self.last_seen: Dict[str, datetime] = {}

    def heartbeat(self, name: str) -> None:
        self.last_seen[name] = datetime.now(timezone.utc)

    def is_stale(self, name: str) -> bool:
        ts = self.last_seen.get(name)
        if not ts:
            return True
        return datetime.now(timezone.utc) - ts > self.max_stale
