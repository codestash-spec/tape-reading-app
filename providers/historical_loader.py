from __future__ import annotations

import csv
import json
import time
from typing import Callable, Iterable, List, Optional

from core.event_bus import EventBus
from models.market_event import MarketEvent


class HistoricalLoader:
    """
    Carrega dados históricos (CSV/JSON) e converte-os em MarketEvents.
    Usado pelo Replay Engine para simular streaming real-time.

    Formatos suportados:
    - CSV com colunas: timestamp, type, symbol, payload_json
    - JSON com lista de eventos MarketEvent serializados
    """

    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.loaded_events: List[MarketEvent] = []

    # ----------------------------------------------------------------------
    # LOADING METHODS
    # ----------------------------------------------------------------------

    def load_csv(self, file_path: str):
        """
        CSV esperado:
        timestamp,type,symbol,payload_json

        payload_json deve ser um dict serializado.
        """
        events = []
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                evt = MarketEvent(
                    timestamp=float(row["timestamp"]),
                    type=row["type"],
                    symbol=row["symbol"],
                    payload=json.loads(row["payload_json"]),
                )
                events.append(evt)

        self.loaded_events = sorted(events, key=lambda e: e.timestamp)
        print(f"[HistoricalLoader] Loaded {len(self.loaded_events)} events from CSV.")

    def load_json(self, file_path: str):
        """
        JSON esperado:
        [
            {"timestamp": ..., "type": "...", "symbol": "...", "payload": {...}},
            ...
        ]
        """
        with open(file_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        events = [
            MarketEvent(
                timestamp=e["timestamp"],
                type=e["type"],
                symbol=e["symbol"],
                payload=e["payload"],
            )
            for e in raw_list
        ]

        self.loaded_events = sorted(events, key=lambda e: e.timestamp)
        print(f"[HistoricalLoader] Loaded {len(self.loaded_events)} events from JSON.")

    # ----------------------------------------------------------------------
    # REPLAY MODE
    # ----------------------------------------------------------------------

    def replay(self, speed: float = 1.0, on_event: Optional[Callable] = None):
        """
        Reproduz os eventos históricos como se fossem real-time.
        speed = 1.0 → tempo real
        speed = 2.0 → 2x mais rápido
        speed = 10.0 → 10x mais rápido

        on_event(optional): callback para debugging (antes de publicar no bus)
        """

        if not self.loaded_events:
            print("[HistoricalLoader] No events loaded.")
            return

        print(f"[HistoricalLoader] Starting replay: {len(self.loaded_events)} events...")

        start_t = self.loaded_events[0].timestamp

        for i, evt in enumerate(self.loaded_events):
            if i > 0:
                prev = self.loaded_events[i - 1].timestamp
                delay = (evt.timestamp - prev) / speed
                if delay > 0:
                    time.sleep(delay)

            if on_event:
                on_event(evt)

            self.bus.publish(evt.type, evt)

        print("[HistoricalLoader] Replay completed.")

    # ----------------------------------------------------------------------
    # UTILS
    # ----------------------------------------------------------------------

    def clear(self):
        """Limpa o buffer interno."""
        self.loaded_events = []
