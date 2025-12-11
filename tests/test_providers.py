import json
import os
import time
from datetime import datetime, timezone

import pytest

from providers.historical_loader import HistoricalLoader
from providers.replay_clock import paced_events
from core.event_bus import EventBus
from models.market_event import MarketEvent


def test_historical_loader_orders_events(tmp_path):
    bus = EventBus()
    loader = HistoricalLoader(bus)
    path = tmp_path / "data.json"
    events = [
        {
            "timestamp": datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc).isoformat(),
            "event_type": "tick",
            "symbol": "ES",
            "payload": {"p": 1},
        },
        {
            "timestamp": datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc).isoformat(),
            "event_type": "tick",
            "symbol": "ES",
            "payload": {"p": 2},
        },
    ]
    path.write_text(json.dumps(events))
    loader.load_json(str(path))
    assert len(loader.loaded_events) == 2
    assert loader.loaded_events[0].payload["p"] == 1
    bus.stop()


def test_replay_clock_pacing(monkeypatch):
    delays = []

    def fake_sleep(x):
        delays.append(x)

    monkeypatch.setattr(time, "sleep", fake_sleep)
    events = [(0.0, "a"), (1.0, "b"), (3.0, "c")]
    out = list(paced_events(events, speed=2.0))
    assert out == ["a", "b", "c"]
    assert pytest.approx(sum(delays), rel=1e-2) == 1.5
