import json
import time
from datetime import datetime, timezone

import pytest

from core.event_bus import EventBus
from providers.historical_loader import HistoricalLoader
from ui.event_bridge import EventBridge


@pytest.mark.qt
def test_event_bridge_receives_replay(qtbot, tmp_path):
    bus = EventBus()
    bridge = EventBridge(bus)
    bridge.start(["dom_snapshot", "trade"])
    dom_hits = []
    trade_hits = []
    bridge.domUpdated.connect(lambda p: dom_hits.append(p))
    bridge.tapeUpdated.connect(lambda p: trade_hits.append(p))

    events = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "dom_snapshot",
            "symbol": "ES",
            "payload": {"bid": 100, "ask": 100.5},
        },
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "trade",
            "symbol": "ES",
            "payload": {"price": 100.25, "size": 1},
        },
    ]
    path = tmp_path / "events.json"
    path.write_text(json.dumps(events))
    loader = HistoricalLoader(bus)
    loader.load_json(str(path))
    loader.replay(speed=10.0)
    qtbot.wait(200)
    bus.stop()
    assert dom_hits and trade_hits
