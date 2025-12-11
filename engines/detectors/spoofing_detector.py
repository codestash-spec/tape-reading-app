from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any

from core.event_bus import EventBus
from models.market_event import MarketEvent


class SpoofingDetector:
    """
    Simple spoofing detector: looks for rapid add/remove asymmetry on DOM levels.
    Emits alert_event with type='spoof'.
    """

    def __init__(self, bus: EventBus, window: int = 10, ratio: float = 3.0) -> None:
        self.bus = bus
        self.window = window
        self.ratio = ratio
        self.history: Dict[str, deque[Dict[str, Any]]] = {}
        self.bus.subscribe("dom_snapshot", self.on_dom)

    def on_dom(self, evt: MarketEvent) -> None:
        sym = evt.symbol
        payload = evt.payload or {}
        dom = payload.get("dom") or payload.get("ladder") or []
        dq = self.history.setdefault(sym, deque(maxlen=self.window))
        levels = []
        if isinstance(dom, list):
            for level in dom:
                try:
                    price = float(level.get("price"))
                    bid = float(level.get("bid_size", level.get("bid", 0.0)))
                    ask = float(level.get("ask_size", level.get("ask", 0.0)))
                    levels.append((price, bid, ask))
                except Exception:
                    continue
        dq.append({"ts": evt.timestamp, "levels": levels})
        if len(dq) < 2:
            return
        # Compare last vs prev
        prev = dq[-2]["levels"]
        added_bid = sum(max(b - pb, 0) for (p, b, a), (pp, pb, pa) in zip(levels, prev) if abs(p - pp) < 1e-6)
        removed_bid = sum(max(pb - b, 0) for (p, b, a), (pp, pb, pa) in zip(levels, prev) if abs(p - pp) < 1e-6)
        added_ask = sum(max(a - pa, 0) for (p, b, a), (pp, pb, pa) in zip(levels, prev) if abs(p - pp) < 1e-6)
        removed_ask = sum(max(pa - a, 0) for (p, b, a), (pp, pb, pa) in zip(levels, prev) if abs(p - pp) < 1e-6)

        spoof_bid = added_bid > removed_bid * self.ratio and added_bid > 0
        spoof_ask = added_ask > removed_ask * self.ratio and added_ask > 0
        if spoof_bid or spoof_ask:
            side = "bid" if spoof_bid else "ask"
            self._emit(sym, side, added_bid, added_ask, removed_bid, removed_ask)

    def _emit(self, symbol: str, side: str, add_b: float, add_a: float, rem_b: float, rem_a: float) -> None:
        evt = MarketEvent(
            event_type="alert_event",
            timestamp=datetime.now(timezone.utc),
            source="spoof_detector",
            symbol=symbol,
            payload={
                "type": "spoof",
                "side": side,
                "added_bid": add_b,
                "added_ask": add_a,
                "removed_bid": rem_b,
                "removed_ask": rem_a,
            },
        )
        self.bus.publish(evt)
