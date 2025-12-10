from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class TraceSpan:
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str | None = None
    duration_ms: float | None = None
    error: str | None = None

    def finish(self, duration_ms: float, status: str = "ok", error: str | None = None) -> None:
        self.duration_ms = duration_ms
        self.status = status
        self.error = error
