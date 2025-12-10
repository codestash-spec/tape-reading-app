from __future__ import annotations

from typing import Dict, List


class ConfluenceFramework:
    """
    Applies additional filters (volatility regime, liquidity signals, tags).
    """

    def validate(self, snapshot: Dict, features: Dict[str, float], tags: List[str]) -> bool:
        vol = features.get("volatility", 0.0)
        if vol and vol > 5.0:
            return False
        if features.get("liq_spoof", 0.0) > 0:
            return False
        return True
