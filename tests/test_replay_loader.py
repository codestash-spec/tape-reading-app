from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from providers.historical_loader import HistoricalLoader


def test_replay_orders_events_and_invokes_callback(tmp_path: Path, event_bus, sample_event):
    """HistoricalLoader should order events by timestamp and honor speed control."""
    now = datetime.now(timezone.utc)
    events = [
        {
            "timestamp": now.isoformat(),
            "event_type": "tick",
            "symbol": "ES",
            "source": "replay",
            "payload": {"p": 10},
        },
        {
            "timestamp": (now + timedelta(seconds=1)).isoformat(),
            "event_type": "tick",
            "symbol": "ES",
            "source": "replay",
            "payload": {"p": 11},
        },
    ]
    json_path = tmp_path / "events.json"
    json_path.write_text(json.dumps(events))

    loader = HistoricalLoader(event_bus)
    loader.load_json(str(json_path))

    seen = []
    loader.replay(speed=1000, on_event=lambda evt: seen.append(evt))

    assert [evt.payload["p"] for evt in seen] == [10, 11]
    assert all(evt.source == "replay" for evt in seen)
