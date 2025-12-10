from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict


class HealthStatus:
    def __init__(self) -> None:
        self.components: Dict[str, str] = {}

    def set(self, name: str, status: str) -> None:
        self.components[name] = status

    def snapshot(self) -> Dict[str, str]:
        return {**self.components, "timestamp": datetime.now(timezone.utc).isoformat()}
