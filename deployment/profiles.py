from __future__ import annotations

from typing import Dict


def profile_config(env: str) -> Dict[str, str]:
    if env == "prod":
        return {"mode": "ibkr", "observability": "full"}
    if env == "paper":
        return {"mode": "sim", "observability": "standard"}
    return {"mode": "sim", "observability": "dev"}
