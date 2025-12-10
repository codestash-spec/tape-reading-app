from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from models.market_event import MarketEvent


@dataclass
class TapeStats:
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    trades: int = 0
    absorption_score: float = 0.0
    last_price: float = 0.0
    window: List[float] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.window is None:
            self.window = []


class AdvancedTapeEngine:
    """
    Processes reconstructed trades, tags aggressor side, estimates absorption.
    """

    def __init__(self, window_seconds: int = 5, absorption_threshold: float = 1000.0) -> None:
        self.window_seconds = window_seconds
        self.absorption_threshold = absorption_threshold
        self.state: Dict[str, TapeStats] = {}
        self._history: Dict[str, List[tuple[datetime, float]]] = {}

    def on_trade(self, evt: MarketEvent) -> TapeStats:
        symbol = evt.symbol
        payload = evt.payload or {}
        price = float(payload.get("price") or payload.get("last") or 0.0)
        size = float(payload.get("size", payload.get("qty", 0.0)) or 0.0)
        side = payload.get("side") or payload.get("aggressor")
        mid = payload.get("mid")
        stats = self.state.get(symbol, TapeStats())

        if side == "buy":
            stats.buy_volume += size
        elif side == "sell":
            stats.sell_volume += size
        else:
            if mid is not None and price >= mid:
                stats.buy_volume += size
                side = "buy"
            elif mid is not None:
                stats.sell_volume += size
                side = "sell"

        stats.trades += 1
        stats.last_price = price

        self._update_history(symbol, size)
        stats.absorption_score = self._calc_absorption(symbol)
        self.state[symbol] = stats
        return stats

    def _update_history(self, symbol: str, size: float) -> None:
        ts = datetime.now(timezone.utc)
        hist = self._history.get(symbol, [])
        hist.append((ts, size))
        cutoff = ts - timedelta(seconds=self.window_seconds)
        hist = [(t, s) for t, s in hist if t >= cutoff]
        self._history[symbol] = hist

    def _calc_absorption(self, symbol: str) -> float:
        hist = self._history.get(symbol, [])
        vol = sum(s for _, s in hist)
        return vol / self.absorption_threshold if self.absorption_threshold else 0.0
