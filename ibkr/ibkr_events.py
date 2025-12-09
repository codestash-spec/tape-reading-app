"""
ibkr_events.py

Camada de normalização de eventos da IBKR para o modelo institucional de MarketEvent.

Responsabilidades:
- Traduzir callbacks brutos da IBAPI (tick-by-tick, DOM, trades).
- Normalizar dados em estruturas universais (tick, trade, DOM).
- Construir objetos MarketEvent compatíveis com o EventBus.
- Manter uma interface clara e estável para o ibkr_connector.py.

Este módulo **não** depende de threads, sockets ou UI. É puramente funcional:
input = dados IBKR, output = MarketEvent pronto a ser publicado.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

# Importa o modelo universal de evento já existente no projeto.
# ❗ Import mínimo para não acoplar demais.
from models.market_event import MarketEvent  # type: ignore[import]


# =============================================================================
#  CONFIGURAÇÃO DE MAPEAMENTO PARA MarketEvent
# =============================================================================


class MarketEventMapping(BaseModel):
    """
    Adapta este módulo ao schema real de MarketEvent sem alterar código.

    Ajusta estes campos se o teu MarketEvent tiver nomes diferentes, por exemplo:
      - "provider" em vez de "source"
      - "instrument" em vez de "symbol"
      - "timestamp" em vez de "ts"
      - "data" em vez de "payload"
    """

    model_config = ConfigDict(frozen=True)

    source_field: str = "source"
    symbol_field: str = "symbol"
    type_field: str = "event_type"
    ts_field: str = "ts"
    payload_field: str = "payload"

    # Valor fixo para identificar o provider
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
    Constrói um MarketEvent usando o esquema de fields configurável.

    Isto garante compatibilidade mesmo que o MarketEvent mude de assinatura,
    bastando ajustar o MarketEventMapping acima.
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
#  ENUMS / TIPOS UNIVERSAIS
# =============================================================================


class EventKind(str, Enum):
    """Tipos universais de eventos que saem deste módulo."""

    TICK = "tick"          # bid/ask atualizado, mid, spread
    TRADE = "trade"        # negócio/time & sales
    DOM_DELTA = "dom_delta"  # atualização incremental do livro
    DOM_SNAPSHOT = "dom_snapshot"  # snapshot completo (opcional / futuro)


class DOMSide(str, Enum):
    BID = "bid"
    ASK = "ask"

    @staticmethod
    def from_ib_side(side: int) -> "DOMSide":
        # IB API → 0 = ask, 1 = bid
        if side == 1:
            return DOMSide.BID
        return DOMSide.ASK


class DOMOperation(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"

    @staticmethod
    def from_ib_op(op: int) -> "DOMOperation":
        # IB API → 0 = insert, 1 = update, 2 = delete
        if op == 0:
            return DOMOperation.INSERT
        if op == 1:
            return DOMOperation.UPDATE
        return DOMOperation.DELETE


class AggressorSide(str, Enum):
    """Lado agressor do negócio (para delta/footprint)."""

    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


# =============================================================================
#  MODELOS NORMALIZADOS (Pydantic v2, imutáveis)
# =============================================================================


class NormalizedTick(BaseModel):
    """
    Tick normalizado (bid/ask) para todos os engines.

    Pode ser criado tanto a partir de tick-by-tick bid/ask como de snapshots.
    """

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

    # Campo raw opcional para debug/telemetria
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
        last_size: float,
        raw: Optional[Dict[str, Any]] = None,
    ) -> "NormalizedTick":
        # Versão minimalista quando só temos last/last_size
        return cls(
            symbol=symbol,
            ts=ts,
            last=last,
            last_size=last_size,
            raw=raw,
        )


class NormalizedTrade(BaseModel):
    """
    Negócio (trade) normalizado, ideal para Delta/Footprint.

    Normaliza time & sales da IB (tickByTickAllLast) num formato único.
    """

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
    """
    Nível do livro (DOM Level).

    Usado tanto para snapshots como para reconstrução incremental no DOM Engine.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime

    side: DOMSide
    level: int  # posição no livro, 0 = melhor preço
    price: float
    size: float

    market_maker: Optional[str] = None
    is_smart_depth: Optional[bool] = None

    raw: Optional[Dict[str, Any]] = None


class DOMDelta(BaseModel):
    """
    Atualização incremental do livro (DOM).

    Representa o que veio num único callback updateMktDepth/UpdateMktDepthL2.
    """

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
    """
    Snapshot completo do livro (bids/asks).

    Pode ser usado num futuro "replay" ou como estado inicial para o DOM Engine.
    """

    model_config = ConfigDict(frozen=True, extra="ignore")

    symbol: str
    ts: datetime

    bids: List[DOMLevel] = Field(default_factory=list)
    asks: List[DOMLevel] = Field(default_factory=list)

    raw: Optional[Dict[str, Any]] = None


# =============================================================================
#  BUILDERS PÚBLICOS → IBKR RAW → MarketEvent
# =============================================================================
#
# Estes são os métodos que o ibkr_connector.py deve usar diretamente,
# idealmente mapeando 1:1 com callbacks da IBAPI.
#
# Cada função devolve **um único** MarketEvent universal.
# =============================================================================


# ----------------------------
#  TICK BY TICK BID/ASK
# ----------------------------


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
    Constrói um MarketEvent de tipo 'tick' a partir de tick-by-tick bid/ask da IB.

    Ideal para mapear diretamente de:
      tickByTickBidAsk(reqId, time, bidPrice, askPrice, bidSize, askSize, bidAttribs, askAttribs)
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


# ----------------------------
#  TICK BY TICK LAST TRADE
# ----------------------------


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
    Constrói um MarketEvent de tipo 'trade'.

    Para mapear:
      tickByTickAllLast(reqId, tickType, time, price, size, tickAttribLast, exchange, specialConditions)

    O lado agressor pode ser inferido externamente (p.ex. via comparação com mid)
    e passado aqui, ou mantido como UNKNOWN.
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


# ----------------------------
#  TICKS SIMPLIFICADOS (LAST ONLY)
# ----------------------------


def build_tick_from_last(
    *,
    symbol: str,
    time: int | float,
    last_price: float,
    last_size: float,
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Constrói um evento 'tick' minimalista quando só tens last/last_size.

    Útil para FX/CFD onde não tens DOM completo, mas queres manter formato único.
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


# ----------------------------
#  DOM DELTA (updateMktDepth / L2)
# ----------------------------


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
    Constrói um MarketEvent de tipo 'dom_delta' a partir de updateMktDepthL2.

    IB API:
      updateMktDepthL2(
        reqId, position, marketMaker, operation,
        side, price, size, isSmartDepth
      )
    """
    if time is None:
        ts = datetime.now(timezone.utc)
    else:
        ts = datetime.fromtimestamp(float(time), tz=timezone.utc)

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


# ----------------------------
#  DOM SNAPSHOT (OPCIONAL / FUTURO)
# ----------------------------


def build_dom_snapshot(
    *,
    symbol: str,
    ts: Optional[datetime],
    bids: Iterable[DOMLevel],
    asks: Iterable[DOMLevel],
    raw: Optional[Dict[str, Any]] = None,
) -> MarketEvent:
    """
    Constrói um MarketEvent de tipo 'dom_snapshot'.

    Este método não é usado diretamente pela IBAPI (não há snapshot nativo),
    mas serve para:
      - Reconstruções de replay.
      - Consulta do estado atual do DOM Engine se exposto como evento.

    O ibkr_connector pode, no futuro, emitir snapshots periódicos
    construídos a partir de um estado interno do DOM.
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
#  HELPERS DE ALTO NÍVEL (OPCIONAIS)
# =============================================================================


def build_from_ib_tick_by_tick_bid_ask(
    *,
    symbol: str,
    time: int | float,
    bid_price: float,
    ask_price: float,
    bid_size: float,
    ask_size: float,
    bid_attribs: Any,
    ask_attribs: Any,
) -> MarketEvent:
    """
    Conveniência para usar diretamente dentro do callback IBAPI
    tickByTickBidAsk.

    Mantém os atributos brutos em `raw` para debug.
    """
    raw = {
        "bid_attribs": repr(bid_attribs),
        "ask_attribs": repr(ask_attribs),
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
    Conveniência para usar diretamente dentro do callback IBAPI
    tickByTickAllLast.

    `aggressor` pode ser inferido externamente e passado aqui, ou
    ficar UNKNOWN.
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
    Conveniência para usar diretamente dentro do callback IBAPI
    updateMktDepthL2.

    O campo `time` pode ser controlado externamente (p.ex. vindo de um
    clock monotónico) ou deixado como None para usar now().
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
