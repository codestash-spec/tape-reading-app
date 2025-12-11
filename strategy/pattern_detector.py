from __future__ import annotations

from typing import Dict


def detect_absorption(delta: float, liquidity_shift: float) -> bool:
    """
    Basic absorption heuristic: large delta with little price progress.
    """
    return abs(delta) > 500 and abs(liquidity_shift) < 1.0


def detect_spoof(added_liquidity: float, removed_liquidity: float) -> bool:
    """
    Spoof when added >> removed and then pulled quickly.
    """
    return added_liquidity > removed_liquidity * 3 and removed_liquidity > 0


def detect_vacuum(imbalance: float, volume_drop: float) -> bool:
    """
    Liquidity vacuum: large imbalance and sudden volume drop.
    """
    return abs(imbalance) > 0.6 and volume_drop > 50


def detect_divergence(delta: float, price_change: float) -> bool:
    """
    Delta-price divergence: strong delta with weak price follow-through.
    """
    return abs(delta) > 300 and abs(price_change) < 0.25


def classify_pattern(features: Dict[str, float]) -> str:
    if detect_absorption(features.get("delta", 0.0), features.get("shift", 0.0)):
        return "absorption"
    if detect_spoof(features.get("added_liq", 0.0), features.get("removed_liq", 0.0)):
        return "spoof"
    if detect_vacuum(features.get("imbalance", 0.0), features.get("volume_drop", 0.0)):
        return "vacuum"
    if detect_divergence(features.get("delta", 0.0), features.get("price_change", 0.0)):
        return "divergence"
    return "none"
