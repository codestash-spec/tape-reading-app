from __future__ import annotations

from typing import Dict, List


class SignalScorer:
    """
    Scores signals using features and tags.
    """

    def score(self, features: Dict[str, float], tags: List[str]) -> float:
        base = abs(features.get("imbalance", 0.0))
        base += abs(features.get("delta", 0.0)) * 0.001
        if "absorption" in tags:
            base += 0.1
        return base
