from __future__ import annotations

from collections import defaultdict
from typing import Dict


class ExecutionMetrics:
    def __init__(self) -> None:
        self.stats: Dict[str, Dict[str, float]] = defaultdict(dict)

    def record_fill(self, symbol: str, slippage_bps: float, latency_ms: float) -> None:
        sym = self.stats[symbol]
        sym["fills"] = sym.get("fills", 0) + 1
        sym["slippage_bps_total"] = sym.get("slippage_bps_total", 0.0) + slippage_bps
        sym["latency_ms_total"] = sym.get("latency_ms_total", 0.0) + latency_ms
        sym["slippage_bps_avg"] = sym["slippage_bps_total"] / sym["fills"]
        sym["latency_ms_avg"] = sym["latency_ms_total"] / sym["fills"]
        self.stats[symbol] = sym
