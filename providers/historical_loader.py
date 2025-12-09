from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional

from core.event_bus import EventBus
from models.market_event import MarketEvent


def _coerce_timestamp(value: float | int | str | datetime) -> datetime:
    """
    Accepts epoch seconds or ISO strings and returns timezone-aware datetime.
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (float, int)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    return datetime.fromisoformat(str(value)).astimezone(timezone.utc)


class HistoricalLoader:
    """
    Loads historical data (CSV/JSON) and replays it as MarketEvents.

    Formats supported:
    - CSV with columns: timestamp, type/event_type, symbol, payload_json, [source]
    - JSON list of serialized MarketEvent-like dicts
    """

    def __init__(self, event_bus: EventBus, source: str = "replay") -> None:
        self.bus = event_bus
        self.source = source
        self.loaded_events: List[MarketEvent] = []

    # ----------------------------------------------------------------------
    # LOADING METHODS
    # ----------------------------------------------------------------------

    def load_csv(self, file_path: str) -> None:
        """
        CSV expected columns:
        timestamp,type,event_type,symbol,payload_json,[source]

        payload_json must contain a serialized dict.
        """
        events: List[MarketEvent] = []
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = _coerce_timestamp(row["timestamp"])
                event_type = row.get("event_type") or row.get("type")
                symbol = row.get("symbol") or ""
                payload = json.loads(row["payload_json"])
                source = row.get("source") or self.source

                evt = MarketEvent(
                    event_type=event_type,
                    timestamp=ts,
                    source=source,
                    symbol=symbol,
                    payload=payload,
                )
                events.append(evt)

        self.loaded_events = sorted(events, key=lambda e: e.timestamp)
        print(f"[HistoricalLoader] Loaded {len(self.loaded_events)} events from CSV.")

    def load_json(self, file_path: str) -> None:
        """
        JSON expected:
        [
            {"timestamp": ..., "event_type": "...", "symbol": "...", "payload": {...}, "source": "..."},
            ...
        ]
        """
        with open(file_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        events: List[MarketEvent] = []
        for entry in raw_list:
            ts = _coerce_timestamp(entry["timestamp"])
            evt = MarketEvent(
                event_type=entry.get("event_type") or entry.get("type"),
                timestamp=ts,
                source=entry.get("source") or self.source,
                symbol=entry["symbol"],
                payload=entry["payload"],
            )
            events.append(evt)

        self.loaded_events = sorted(events, key=lambda e: e.timestamp)
        print(f"[HistoricalLoader] Loaded {len(self.loaded_events)} events from JSON.")

    # ----------------------------------------------------------------------
    # REPLAY MODE
    # ----------------------------------------------------------------------

    def replay(self, speed: float = 1.0, on_event: Optional[Callable[[MarketEvent], None]] = None) -> None:
        """
        Replays loaded events as if they were real-time.
        speed = 1.0 -> real time
        speed = 2.0 -> 2x faster
        speed = 10.0 -> 10x faster

        on_event(optional): callback invoked before publishing to the bus.
        """
        if not self.loaded_events:
            print("[HistoricalLoader] No events loaded.")
            return

        print(f"[HistoricalLoader] Starting replay: {len(self.loaded_events)} events...")

        for i, evt in enumerate(self.loaded_events):
            if i > 0:
                prev = self.loaded_events[i - 1].timestamp
                delay = (evt.timestamp - prev).total_seconds() / max(speed, 0.0001)
                if delay > 0:
                    time.sleep(delay)

            if on_event:
                on_event(evt)

            self.bus.publish(evt)

        print("[HistoricalLoader] Replay completed.")

    # ----------------------------------------------------------------------
    # UTILS
    # ----------------------------------------------------------------------

    def clear(self) -> None:
        """Clear the in-memory buffer."""
        self.loaded_events = []
