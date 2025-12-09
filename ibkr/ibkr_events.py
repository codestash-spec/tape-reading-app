from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.market_event import MarketEvent


# =============================================================================
#  CONFIGURATION FOR MarketEvent ADAPTATION
# =============================================================================


class MarketEventMapping(BaseModel):
    """
    Adapts this module to the actual MarketEvent schema without scattering
    string literals across the codebase.
    """

    model_config = ConfigDict(frozen=True)

    source_field: str = "source"
    symbol_field: str = "symbol"
    type_field: str = "event_type"
    ts_field: str = "timestamp"
    payload_field: str = "payload"

    source_value: str = "ibkr"


MARKET_EVENT_MAPPING = MarketEventMapping()


def _build_market_event(
    *,
    kind: str,
    symbol: str,
    ts: datetime,
    payload: Mapping[str, Any],
) -> MarketEvent:
    """
    Build a MarketEvent using the configured field names.
    """
    cfg = MARKET_EVENT_MAPPING

    kwargs = {
        cfg.source_field: cfg.source_value,
        cfg.symbol_field: symbol,
        cfg.type_field: kind,
        cfg.ts_field: ts,
        cfg.payload_field: payload,
    }

    return MarketEvent(**kwargs)  # type: ignore[arg-type]


# =============================================================================
#  ENUMS / TYPES
# =============================================================================


class EventKind(str, Enum):
    """Universal event kinds leaving this module."""

    TICK = "tick"
    TRADE = "trade"
    DOM_DELTA = "dom_delta"
    DOM_SNAPSHOT = "dom_snapshot"


class DOMSide(str, Enum):
    BID = "bid"
    ASK = "ask"

    @staticmethod
    def from_ib_side(side: int) -> "DOMSide":
        # IB API: 0 = ask, 1 = bid
        return DOMSide.BID if side == 1 else DOMSide.ASK


class DOMOperation(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

    @staticmethod
    def from_ib_op(op: int) -> "DOMOperation":
        # IB API: 0 = insert, 1 = update, 2 = delete
        if op == 0:
            return DOMOperation.INSERT
        if op == 1:
            return DOMOperation.UPDATE
        return DOMOperation.DELETE


class AggressorSide(str, Enum):
    """Aggressor side of a trade, useful for delta/footprint engines."""

    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


# =============================================================================
#  NORMALIZED MODELS (Pydantic v2, immutable)
# =============================================================================


class NormalizedTick(BaseModel):
    """Normalized tick (bid/ask/last) consumed by engines."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime

    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None

    last: Optional[float] = None
    last_size: Optional[float] = None

    mid: Optional[float] = None
    spread: Optional[float] = None

    raw: Optional[Dict[str, Any]] = None

    @staticmethod
    def compute_mid(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
        if bid is None or ask is None:
            return None
        return (bid + ask) / 2.0

    @staticmethod
    def compute_spread(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
        if bid is None or ask is None:
            return None
        return ask - bid

    @classmethod
    def from_bid_ask(
        cls,
        *,
        symbol: str,
        ts: datetime,
        bid: Optional[float],
        ask: Optional[float],
        bid_size: Optional[float],
        ask_size: Optional[float],
        raw: Optional[Dict[str, Any]] = None,
    ) -> "NormalizedTick":
        mid = cls.compute_mid(bid, ask)
        spread = cls.compute_spread(bid, ask)
        return cls(
            symbol=symbol,
            ts=ts,
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            mid=mid,
            spread=spread,
            raw=raw,
        )

    @classmethod
    def from_last(
        cls,
        *,
        symbol: str,
        ts: datetime,
        last: float,
        last_size: Optional[float],
        raw: Optional[Dict[str, Any]] = None,
    ) -> "NormalizedTick":
        return cls(
            symbol=symbol,
            ts=ts,
            last=last,
            last_size=last_size,
            raw=raw,
        )


class NormalizedTrade(BaseModel):
    """Normalized trade for Delta/Footprint engines."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime
    price: float
    size: float

    aggressor: AggressorSide = AggressorSide.UNKNOWN
    exchange: Optional[str] = None
    special_conditions: Optional[str] = None

    raw: Optional[Dict[str, Any]] = None


class DOMLevel(BaseModel):
    """DOM level used for snapshots."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime

    side: DOMSide
    level: int  # position in the book, 0 = best price
    price: float
    size: float

    market_maker: Optional[str] = None
    is_smart_depth: Optional[bool] = None

    raw: Optional[Dict[str, Any]] = None


class DOMDelta(BaseModel):
    """Incremental DOM update (from updateMktDepth/UpdateMktDepthL2)."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime

    operation: DOMOperation
    level: int
    side: DOMSide

    price: Optional[float] = None
    size: Optional[float] = None

    market_maker: Optional[str] = None
    is_smart_depth: Optional[bool] = None

    raw: Optional[Dict[str, Any]] = None


class DOMSnapshot(BaseModel):
    """Full DOM snapshot (bids/asks)."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime

    bids: List[DOMLevel] = Field(default_factory=list)
    asks: List[DOMLevel] = Field(default_factory=list)

    raw: Optional[Dict[str, Any]] = None


# =============================================================================
#  BUILDERS: IBKR RAW -> MarketEvent
# =============================================================================


def build_tick_from_bid_ask(
    *,
    symbol: str,
    time: int | float,
    bid_price: float,
    ask_price: float,
    bid_size: float,
    ask_size: float,
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Build a 'tick' MarketEvent from tick-by-tick bid/ask.
    """
    ts = datetime.fromtimestamp(float(time), tz=timezone.utc)

    tick = NormalizedTick.from_bid_ask(
        symbol=symbol,
        ts=ts,
        bid=bid_price,
        ask=ask_price,
        bid_size=bid_size,
        ask_size=ask_size,
        raw=raw,
    )

    return _build_market_event(
        kind=EventKind.TICK.value,
        symbol=symbol,
        ts=ts,
        payload=tick.model_dump(),
    )


def build_trade_from_last(
    *,
    symbol: str,
    time: int | float,
    price: float,
    size: float,
    aggressor: AggressorSide = AggressorSide.UNKNOWN,
    exchange: Optional[str] = None,
    special_conditions: Optional[str] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Build a 'trade' MarketEvent from tickByTickAllLast.
    """
    ts = datetime.fromtimestamp(float(time), tz=timezone.utc)

    trade = NormalizedTrade(
        symbol=symbol,
        ts=ts,
        price=price,
        size=size,
        aggressor=aggressor,
        exchange=exchange,
        special_conditions=special_conditions,
        raw=raw,
    )

    return _build_market_event(
        kind=EventKind.TRADE.value,
        symbol=symbol,
        ts=ts,
        payload=trade.model_dump(),
    )


def build_tick_from_last(
    *,
    symbol: str,
    time: int | float,
    last_price: float,
    last_size: Optional[float],
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Build a minimalist 'tick' event when only last/size is available.
    """
    ts = datetime.fromtimestamp(float(time), tz=timezone.utc)

    tick = NormalizedTick.from_last(
        symbol=symbol,
        ts=ts,
        last=last_price,
        last_size=last_size,
        raw=raw,
    )

    return _build_market_event(
        kind=EventKind.TICK.value,
        symbol=symbol,
        ts=ts,
        payload=tick.model_dump(),
    )


def build_dom_delta_from_l2(
    *,
    symbol: str,
    time: Optional[int | float],
    position: int,
    market_maker: Optional[str],
    operation: int,
    side: int,
    price: float,
    size: float,
    is_smart_depth: Optional[bool] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Build a 'dom_delta' MarketEvent from updateMktDepthL2.
    """
    ts = datetime.fromtimestamp(float(time), tz=timezone.utc) if time is not None else datetime.now(timezone.utc)

    dom_delta = DOMDelta(
        symbol=symbol,
        ts=ts,
        operation=DOMOperation.from_ib_op(operation),
        level=position,
        side=DOMSide.from_ib_side(side),
        price=price,
        size=size,
        market_maker=market_maker,
        is_smart_depth=is_smart_depth,
        raw=raw,
    )

    return _build_market_event(
        kind=EventKind.DOM_DELTA.value,
        symbol=symbol,
        ts=ts,
        payload=dom_delta.model_dump(),
    )


def build_dom_snapshot(
    *,
    symbol: str,
    ts: Optional[datetime],
    bids: Iterable[DOMLevel],
    asks: Iterable[DOMLevel],
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Build a 'dom_snapshot' MarketEvent.
    """
    ts_final = ts or datetime.now(timezone.utc)

    snapshot = DOMSnapshot(
        symbol=symbol,
        ts=ts_final,
        bids=list(bids),
        asks=list(asks),
        raw=raw,
    )

    return _build_market_event(
        kind=EventKind.DOM_SNAPSHOT.value,
        symbol=symbol,
        ts=ts_final,
        payload=snapshot.model_dump(),
    )


# =============================================================================
#  IBKR-SPECIFIC CONVENIENCE BUILDERS
# =============================================================================


def build_from_ib_tick_by_tick_bid_ask(
    *,
    symbol: str,
    time: int | float,
    bid_price: float,
    ask_price: float,
    bid_size: float,
    ask_size: float,
    tick_attribs: Any,
) -> MarketEvent:
    """
    Convenience helper for IBAPI tickByTickBidAsk callback.
    """
    raw = {
        "tick_attribs": repr(tick_attribs),
    }

    return build_tick_from_bid_ask(
        symbol=symbol,
        time=time,
        bid_price=bid_price,
        ask_price=ask_price,
        bid_size=bid_size,
        ask_size=ask_size,
        raw=raw,
    )


def build_from_ib_tick_by_tick_all_last(
    *,
    symbol: str,
    time: int | float,
    price: float,
    size: float,
    tick_attrib_last: Any,
    exchange: Optional[str],
    special_conditions: Optional[str],
    aggressor: AggressorSide = AggressorSide.UNKNOWN,
) -> MarketEvent:
    """
    Convenience helper for IBAPI tickByTickAllLast callback.
    """
    raw = {
        "tick_attrib_last": repr(tick_attrib_last),
    }

    return build_trade_from_last(
        symbol=symbol,
        time=time,
        price=price,
        size=size,
        aggressor=aggressor,
        exchange=exchange,
        special_conditions=special_conditions,
        raw=raw,
    )


def build_from_ib_update_mkt_depth_l2(
    *,
    symbol: str,
    position: int,
    market_maker: str,
    operation: int,
    side: int,
    price: float,
    size: float,
    is_smart_depth: bool,
    time: Optional[int | float] = None,
) -> MarketEvent:
    """
    Convenience helper for IBAPI updateMktDepthL2 callback.
    """
    raw = {
        "market_maker": market_maker,
    }

    return build_dom_delta_from_l2(
        symbol=symbol,
        time=time,
        position=position,
        market_maker=market_maker,
        operation=operation,
        side=side,
        price=price,
        size=size,
        is_smart_depth=is_smart_depth,
        raw=raw,
    )


def build_from_ib_l1_tick(
    *,
    symbol: str,
    tick_type: int,
    price: float,
    size: Optional[float] = None,
    time: Optional[int | float] = None,
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Build a 'tick' event from legacy Level 1 callbacks (tickPrice/tickSize).

    tick_type follows IB TickType enums. Only a subset is handled explicitly.
    """
    ts = datetime.fromtimestamp(float(time), tz=timezone.utc) if time is not None else datetime.now(timezone.utc)
    raw_payload = raw or {}
    raw_payload["tick_type"] = tick_type

    bid = ask = None
    bid_size = ask_size = None
    last = last_size = None

    if tick_type == 1:  # bid price
        bid = price
    elif tick_type == 2:  # ask price
        ask = price
    elif tick_type == 4:  # last price
        last = price
        last_size = size
    else:
        last = price
        last_size = size

    tick = NormalizedTick(
        symbol=symbol,
        ts=ts,
        bid=bid,
        ask=ask,
        bid_size=bid_size,
        ask_size=ask_size,
        last=last,
        last_size=last_size,
        mid=NormalizedTick.compute_mid(bid, ask),
        spread=NormalizedTick.compute_spread(bid, ask),
        raw=raw_payload,
    )

    return _build_market_event(
        kind=EventKind.TICK.value,
        symbol=symbol,
        ts=ts,
        payload=tick.model_dump(),
    )
