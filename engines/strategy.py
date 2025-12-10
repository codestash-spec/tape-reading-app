from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Iterable

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.signal import Signal
from models.state import SymbolState

log = logging.getLogger(__name__)


class Strategy:
    """
    Base strategy: subscribes to market data events and emits signals.
    """

    def __init__(self, bus: EventBus, symbols: Iterable[str]) -> None:
        self.bus = bus
        self.symbols = set(symbols)
        self.state: Dict[str, SymbolState] = {s: SymbolState() for s in symbols}

    def on_start(self) -> None:
        for et in ("tick", "trade", "dom_delta", "dom_snapshot"):
            self.bus.subscribe(et, self.on_event)

    def on_stop(self) -> None:
        pass

    def on_event(self, evt: MarketEvent) -> None:
        raise NotImplementedError

    def emit_signal(self, signal: Signal) -> None:
        evt = MarketEvent(
            event_type="signal",
            timestamp=signal.timestamp,
            source="strategy",
            symbol=signal.symbol,
            payload=signal.model_dump(),
        )
        self.bus.publish(evt)


class MicroPriceMomentumStrategy(Strategy):
    """
    Minimal strategy:
    - Tracks last mid price per symbol from tick events
    - Emits buy signal on upward move, sell on downward move
    """

    def __init__(self, bus: EventBus, symbols: Iterable[str], threshold: float = 0.0) -> None:
        super().__init__(bus, symbols)
        self.threshold = threshold
        self.last_mid: Dict[str, float] = {s: 0.0 for s in symbols}

    def on_event(self, evt: MarketEvent) -> None:
        if evt.event_type != "tick":
            return
        sym = evt.symbol
        mid = evt.payload.get("mid") or evt.payload.get("price") or evt.payload.get("last")
        if mid is None:
            return
        mid = float(mid)
        prev = self.last_mid.get(sym, 0.0)
        self.last_mid[sym] = mid
        if prev == 0.0:
            return
        delta = mid - prev
        if abs(delta) < self.threshold:
            return
        direction = "buy" if delta > 0 else "sell"
        sig = Signal(
            signal_id=uuid.uuid4().hex,
            timestamp=datetime.now(timezone.utc),
            symbol=sym,
            direction=direction,
            score=delta,
            confidence=min(1.0, abs(delta) / (abs(prev) + 1e-6)),
            features={"mid": mid, "prev_mid": prev, "delta": delta},
        )
        log.debug("Emitting signal %s for %s delta=%s", sig.signal_id, sym, delta)
        self.emit_signal(sig)
