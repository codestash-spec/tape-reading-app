from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Deque

from core.event_bus import EventBus
from models.market_event import MarketEvent


@dataclass
class LiquidityState:
    resting: Dict[float, Dict[str, float]] = field(default_factory=dict)
    history: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=50))


class LiquidityMapEngine:
    """
    Tracks resting liquidity, spoof-like patterns, absorption/exhaustion.
    Emits liquidity_update events.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.state: Dict[str, LiquidityState] = {}
        self.bus.subscribe("dom_snapshot", self.on_dom)
        self.bus.subscribe("trade", self.on_trade)

    def on_dom(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        payload = evt.payload or {}
        dom = payload.get("dom") or []
        st = self.state.setdefault(sym, LiquidityState())
        liq_map: Dict[float, Dict[str, float]] = {}
        for level in dom:
            try:
                price = float(level.get("price"))
                bid = float(level.get("bid_size", 0.0))
                ask = float(level.get("ask_size", 0.0))
            except Exception:
                continue
            liq_map[price] = {"bid": bid, "ask": ask}
        st.resting = liq_map
        st.history.append({"ts": evt.timestamp, "resting": liq_map})
        self._emit(sym, st)

    def on_trade(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        st = self.state.setdefault(sym, LiquidityState())
        # For now, just note trade size to check exhaustion
        st.history.append({"ts": evt.timestamp, "trade": evt.payload})
        self._emit(sym, st)

    def _emit(self, symbol: str, st: LiquidityState) -> None:
        ts = datetime.now(timezone.utc)
        payload = {"resting": st.resting, "history_len": len(st.history)}
        evt = MarketEvent(
            event_type="liquidity_update",
            timestamp=ts,
            source="liquidity_map",
            symbol=symbol,
            payload=payload,
        )
        self.bus.publish(evt)
