from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Iterable

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.signal import Signal
from strategy.playbook import PlaybookEngine
from strategy.confluence import ConfluenceFramework
from strategy.regime import RegimeEngine
from strategy.scoring import SignalScorer


class StrategyOrchestrator:
    """
    Consumes microstructure snapshots, applies playbook+confluence+regime filters and emits signals.
    """

    def __init__(self, bus: EventBus, symbols: Iterable[str]) -> None:
        self.bus = bus
        self.symbols = set(symbols)
        self.playbook = PlaybookEngine()
        self.confluence = ConfluenceFramework()
        self.regime = RegimeEngine()
        self.scorer = SignalScorer()
        self.cooldowns: Dict[str, datetime] = {}
        self.cooldown_seconds = 1.0

    def start(self) -> None:
        self.bus.subscribe("microstructure", self.on_microstructure)
        self._subs = ("microstructure",)

    def stop(self) -> None:
        for et in getattr(self, "_subs", ()):
            self.bus.unsubscribe(et, self.on_microstructure)

    def on_microstructure(self, evt: MarketEvent) -> None:
        symbol = evt.symbol
        if symbol not in self.symbols:
            return
        snapshot = evt.payload.get("snapshot", {})
        features = snapshot.get("features", {})
        tags = snapshot.get("tags", [])
        if not self.regime.is_allowed(snapshot):
            return
        decision = self.playbook.evaluate(snapshot, features, tags)
        if not decision.get("action"):
            return
        if decision.get("action") == "skip":
            return
        if not self.confluence.validate(snapshot, features, tags):
            return
        score = self.scorer.score(features, tags)
        if score <= 0:
            return
        ts = datetime.now(timezone.utc)
        signal = Signal(
            signal_id=uuid.uuid4().hex,
            timestamp=ts,
            symbol=symbol,
            direction=decision.get("direction", "flat"),
            score=score,
            confidence=min(1.0, score),
            features=features,
            metadata={"tags": ",".join(tags)},
        )
        out_evt = MarketEvent(
            event_type="signal",
            timestamp=ts,
            source="strategy_orchestrator",
            symbol=symbol,
            payload=signal.model_dump(),
        )
        self.bus.publish(out_evt)
