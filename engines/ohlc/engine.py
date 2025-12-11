from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from core.event_bus import EventBus
from models.market_event import MarketEvent


class OHLCEngine:
    """
    Simple OHLC aggregator from trades/quotes.
    Emits chart_ohlc events with timeframe buckets.
    """

    def __init__(self, bus: EventBus, timeframe_seconds: int = 1) -> None:
        self.bus = bus
        self.tf = timeframe_seconds
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.bus.subscribe("trade", self.on_trade)
        self.bus.subscribe("quote", self.on_quote)

    def _bucket_key(self, ts: datetime) -> int:
        return int(ts.timestamp()) // self.tf

    def on_trade(self, evt: MarketEvent) -> None:
        self._ingest(evt.symbol, evt.payload.get("price"), evt.payload.get("size", 0.0), evt.timestamp)

    def on_quote(self, evt: MarketEvent) -> None:
        # Use last/mid as price proxy
        px = evt.payload.get("last") or evt.payload.get("mid")
        self._ingest(evt.symbol, px, 0.0, evt.timestamp)

    def _ingest(self, symbol: str, price, size, ts: datetime) -> None:
        if price is None:
            return
        try:
            p = float(price)
        except Exception:
            return
        bucket = self._bucket_key(ts)
        key = f"{symbol}:{bucket}"
        bar = self.buckets.get(key, {"t": bucket, "o": p, "h": p, "l": p, "c": p, "v": 0.0})
        bar["h"] = max(bar["h"], p)
        bar["l"] = min(bar["l"], p)
        bar["c"] = p
        try:
            bar["v"] += float(size or 0.0)
        except Exception:
            pass
        self.buckets[key] = bar
        self._emit(symbol, bar)

    def _emit(self, symbol: str, bar: Dict[str, Any]) -> None:
        evt = MarketEvent(
            event_type="chart_ohlc",
            timestamp=datetime.fromtimestamp(bar["t"] * self.tf, tz=timezone.utc),
            source="ohlc_engine",
            symbol=symbol,
            payload={
                "time": bar["t"] * self.tf,
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"],
            },
        )
        self.bus.publish(evt)
