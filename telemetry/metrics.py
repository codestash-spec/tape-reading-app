from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict


class MetricsSink:
    """
    Minimal in-memory metrics sink for counters and observations.
    """

    def __init__(self) -> None:
        self.counters: DefaultDict[str, float] = defaultdict(float)
        self.gauges: DefaultDict[str, float] = defaultdict(float)

    def incr(self, name: str, value: float = 1.0) -> None:
        self.counters[name] += value

    def observe(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def snapshot(self) -> dict:
        return {"counters": dict(self.counters), "gauges": dict(self.gauges)}
