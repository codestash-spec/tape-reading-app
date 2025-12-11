import os

from core.config import load_settings


def test_load_settings_env_override(monkeypatch, tmp_path):
    base = tmp_path / "settings.yaml"
    base.write_text(
        "env: dev\nsymbols: [ES]\nproviders:\n  ibkr:\n    host: 1.1.1.1\n    port: 4001\n    client_id: 5\ntelemetry:\n  log_level: DEBUG\nexecution:\n  mode: sim\nrisk:\n  symbols: [ES]\n  max_size: 10\n  max_exposure: 20\n  throttle_max: 5\nreplay:\n  speed: 1.0\nui:\n  theme: dark\n"
    )
    monkeypatch.setenv("IBKR_HOST", "9.9.9.9")
    settings = load_settings(str(base))
    assert settings.ibkr_host == "9.9.9.9"
    assert settings.risk_limits["max_size"] == 10


def test_missing_profile_uses_base():
    settings = load_settings("config/settings.yaml")
    assert settings.symbols
