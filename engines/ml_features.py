from __future__ import annotations

from typing import Dict, List


def rolling_mean(values: List[float], window: int) -> float:
    if not values:
        return 0.0
    return sum(values[-window:]) / min(len(values), window)


def build_feature_vector(ticks: List[float]) -> Dict[str, float]:
    return {
        "mean_5": rolling_mean(ticks, 5),
        "mean_10": rolling_mean(ticks, 10),
        "last": ticks[-1] if ticks else 0.0,
    }
