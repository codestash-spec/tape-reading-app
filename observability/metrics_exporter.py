from __future__ import annotations

from typing import Dict


class MetricsExporter:
    """Minimal Prometheus text exporter builder."""

    def __init__(self) -> None:
        self.metrics: Dict[str, float] = {}

    def set_metric(self, name: str, value: float) -> None:
        self.metrics[name] = value

    def render_prometheus(self) -> str:
        lines = [f"# TYPE {k} gauge\n{k} {v}" for k, v in self.metrics.items()]
        return "\n".join(lines)
