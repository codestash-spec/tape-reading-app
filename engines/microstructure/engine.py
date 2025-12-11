from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from core.event_bus import EventBus
from engines.microstructure.depth import DepthEngine
from engines.microstructure.delta import MicroDeltaEngine
from engines.microstructure.snapshot import MicrostructureSnapshot
from engines.microstructure.features import MicrostructureFeatureExtractor
from engines.tape.advanced import AdvancedTapeEngine
from engines.footprint.advanced import FootprintEngineAdvanced
from engines.liquidity.engine import LiquidityEngine
from models.market_event import MarketEvent


class MicrostructureEngine:
    """
    Orchestrates advanced microstructure engines and publishes aggregated snapshots.
    """

    def __init__(self, bus: EventBus, symbols: list[str]) -> None:
        self.bus = bus
        self.symbols = symbols
        self.depth = DepthEngine()
        self.delta = MicroDeltaEngine()
        self.tape = AdvancedTapeEngine()
        self.footprint = FootprintEngineAdvanced()
        self.liquidity = LiquidityEngine()
        self.features = MicrostructureFeatureExtractor()

    def start(self) -> None:
        for et in ("dom_snapshot", "dom_delta", "trade", "tick"):
            self.bus.subscribe(et, self.on_event)
        self._subs = ("dom_snapshot", "dom_delta", "trade", "tick")

    def stop(self) -> None:
        subs = getattr(self, "_subs", ("dom_snapshot", "dom_delta", "trade", "tick"))
        for et in subs:
            self.bus.unsubscribe(et, self.on_event)

    def on_event(self, evt: MarketEvent) -> None:
        symbol = evt.symbol
        if evt.event_type == "dom_snapshot":
            depth_state = self.depth.on_dom(evt)
            snapshot = self._build_snapshot(symbol, depth_state=depth_state)
            self._publish_snapshot(snapshot)
        elif evt.event_type == "dom_delta":
            liq = self.liquidity.on_dom_delta(evt)
            snapshot = self._build_snapshot(symbol, liquidity=liq)
            self._publish_snapshot(snapshot)
        elif evt.event_type == "trade":
            delta_state = self.delta.on_trade(evt)
            tape_state = self.tape.on_trade(evt)
            footprint = self.footprint.on_trade(evt)
            snapshot = self._build_snapshot(symbol, delta_state=delta_state, tape_state=tape_state, footprint=footprint)
            self._publish_snapshot(snapshot)
        elif evt.event_type == "tick":
            # ticks update mid price only
            depth_state = self.depth.state.get(symbol)
            snapshot = self._build_snapshot(symbol, depth_state=depth_state, tick_evt=evt)
            self._publish_snapshot(snapshot)

    def _build_snapshot(self, symbol: str, depth_state=None, delta_state=None, tape_state=None, footprint=None, liquidity=None, tick_evt=None) -> MicrostructureSnapshot:
        ts = datetime.now(timezone.utc)
        depth_state = depth_state or self.depth.state.get(symbol)
        delta_state = delta_state or self.delta.state.get(symbol)
        tape_state = tape_state or self.tape.state.get(symbol)
        footprint = footprint or self.footprint.footprints.get(symbol, {})
        liquidity_state = liquidity or self.liquidity.state.get(symbol)

        bid = depth_state.bid if depth_state else None
        ask = depth_state.ask if depth_state else None
        mid = None
        if tick_evt:
            mid = tick_evt.payload.get("mid") or tick_evt.payload.get("price") or tick_evt.payload.get("last")
        if mid is None and bid and ask:
            mid = (float(bid) + float(ask)) / 2

        snapshot = MicrostructureSnapshot(
            symbol=symbol,
            timestamp=ts,
            mid=float(mid) if mid is not None else None,
            bid=float(bid) if bid is not None else None,
            ask=float(ask) if ask is not None else None,
            bid_size=depth_state.bid_size if depth_state else None,
            ask_size=depth_state.ask_size if depth_state else None,
            imbalance=depth_state.imbalance if depth_state else None,
            queue_position=depth_state.queue_position if depth_state else None,
            liquidity_map=depth_state.liquidity_map if depth_state else {},
            delta=delta_state.cumulative if delta_state else None,
            cumulative_delta=delta_state.cumulative if delta_state else None,
            zero_prints=delta_state.zero_prints if delta_state else 0,
            aggressor_side=None,
            absorption_score=tape_state.absorption_score if tape_state else 0.0,
            footprint=footprint,
            liquidity_signals={
                "iceberg": getattr(liquidity_state, "iceberg", 0.0),
                "spoof": getattr(liquidity_state, "spoof", 0.0),
                "replenishment": getattr(liquidity_state, "replenishment", 0.0),
                "shift": getattr(liquidity_state, "shift", 0.0),
            }
            if liquidity_state
            else {},
            features={},
            tags=[],
        )
        snapshot.features = self.features.extract(snapshot)
        return snapshot

    def _publish_snapshot(self, snapshot: MicrostructureSnapshot) -> None:
        evt = MarketEvent(
            event_type="microstructure",
            timestamp=snapshot.timestamp,
            source="microstructure",
            symbol=snapshot.symbol,
            payload={"snapshot": snapshot.__dict__},
        )
        self.bus.publish(evt)
