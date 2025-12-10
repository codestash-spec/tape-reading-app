from __future__ import annotations

from typing import Dict, List


class PlaybookEngine:
    """
    Encapsulates confluence rules: event -> validation -> action.
    """

    def __init__(self) -> None:
        self.rules: List[Dict[str, float]] = [
            {"min_score": 0.2, "direction": "buy", "feature": "imbalance", "threshold": 0.1},
            {"min_score": 0.2, "direction": "sell", "feature": "imbalance", "threshold": -0.1},
        ]

    def evaluate(self, snapshot: Dict, features: Dict[str, float], tags: List[str]) -> Dict[str, str]:
        for rule in self.rules:
            fval = features.get(rule["feature"], 0.0)
            if rule["direction"] == "buy" and fval >= rule["threshold"]:
                return {"action": "enter", "direction": "buy"}
            if rule["direction"] == "sell" and fval <= rule["threshold"]:
                return {"action": "enter", "direction": "sell"}
        return {"action": None}
