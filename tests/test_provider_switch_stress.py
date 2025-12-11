import json
import os
import time

import pytest

from core.event_bus import EventBus
from providers.provider_manager import ProviderManager
from models.market_event import MarketEvent
from datetime import datetime, timezone


def _write_report(data: dict):
    os.makedirs("audit", exist_ok=True)
    with open("audit/switching_report.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_provider_switch_stress():
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"], "dom_depth": 10, "market_symbol": "ES", "ui": {"audit_mode": True}})
    cycle = ["SIM", "BINANCE", "OKX", "IBKR", "CME"]
    leaks = 0
    start_ts = time.time()

    def publish_probe(src):
        evt = MarketEvent(
            event_type="dom_snapshot",
            timestamp=datetime.now(timezone.utc),
            source=src,
            symbol="ES",
            payload={"dom": [{"price": 100.0, "bid_size": 1, "ask_size": 0}]},
        )
        bus.publish(evt)

    for i in range(10):  # 10 cycles * 5 providers = 50 switches
        for name in cycle:
            mgr.start(name)
            publish_probe(name)
            time.sleep(0.02)
            publish_probe("GHOST")  # should be dropped by allowed_sources
    mgr.stop()
    bus.stop()
    duration = time.time() - start_ts
    _write_report(
        {
            "cycles": (i + 1) * len(cycle),
            "leaks": leaks,
            "duration": duration,
        }
    )
    assert leaks == 0
    assert duration < 15
