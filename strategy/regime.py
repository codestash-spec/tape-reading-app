from __future__ import annotations

from typing import Dict


class RegimeEngine:
    """
    Simple regime filters using ATR/volume/session placeholders.
    """

    def __init__(self, atr_threshold: float = 3.0, volume_threshold: float = 0.0) -> None:
        self.atr_threshold = atr_threshold
        self.volume_threshold = volume_threshold

    def is_allowed(self, snapshot: Dict) -> bool:
        features = snapshot.get("features", {})
        atr = features.get("atr", 0.0)
        vol = features.get("volume", 0.0)
        if atr and atr > self.atr_threshold:
            return False
        if vol and vol < self.volume_threshold:
            return False
        return True
