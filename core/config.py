from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

import yaml


@dataclass(frozen=True)
class Settings:
    env: str
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    symbols: List[str]
    log_level: str
    risk_limits: Dict[str, Any]
    execution: Dict[str, Any]
    telemetry: Dict[str, Any]
    replay: Dict[str, Any]


def _load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings(base_path: str = "config/settings.yaml") -> Settings:
    """
    Load settings from YAML with environment/profile overrides and env vars.
    """
    base = _load_yaml(base_path)
    profile_name = os.getenv("PROFILE")
    if profile_name:
        profile_path = os.path.join("config", "profiles", f"{profile_name}.yaml")
        base.update(_load_yaml(profile_path))

    # environment overrides
    env = os.getenv("ENV", base.get("env", "dev"))
    ibkr_host = os.getenv("IBKR_HOST", base.get("providers", {}).get("ibkr", {}).get("host", "127.0.0.1"))
    ibkr_port = int(os.getenv("IBKR_PORT", base.get("providers", {}).get("ibkr", {}).get("port", 7497)))
    ibkr_client_id = int(
        os.getenv("IBKR_CLIENT_ID", base.get("providers", {}).get("ibkr", {}).get("client_id", 1))
    )
    symbols = base.get("symbols", ["XAUUSD"])
    log_level = os.getenv("LOG_LEVEL", base.get("telemetry", {}).get("log_level", "INFO"))

    risk_limits = base.get("risk", {})
    execution = base.get("execution", {})
    telemetry = base.get("telemetry", {})
    replay = base.get("replay", {})

    return Settings(
        env=env,
        ibkr_host=ibkr_host,
        ibkr_port=ibkr_port,
        ibkr_client_id=ibkr_client_id,
        symbols=symbols,
        log_level=log_level,
        risk_limits=risk_limits,
        execution=execution,
        telemetry=telemetry,
        replay=replay,
    )
