from __future__ import annotations

from typing import Dict

from engines.microstructure.snapshot import MicrostructureSnapshot


class MicrostructureFeatureExtractor:
    """
    Converts a MicrostructureSnapshot into a flat feature dictionary for strategy/ML use.
    """

    def extract(self, snapshot: MicrostructureSnapshot) -> Dict[str, float]:
        f: Dict[str, float] = {}
        f["mid"] = snapshot.mid or 0.0
        f["imbalance"] = snapshot.imbalance or 0.0
        f["queue_position"] = snapshot.queue_position or 0.0
        f["delta"] = snapshot.delta or 0.0
        f["cumulative_delta"] = snapshot.cumulative_delta or 0.0
        f["absorption_score"] = snapshot.absorption_score
        f["zero_prints"] = float(snapshot.zero_prints)
        for k, v in snapshot.liquidity_signals.items():
            f[f"liq_{k}"] = v
        for tag in snapshot.tags:
            f[f"tag_{tag}"] = 1.0
        return f
