from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from ibapi.common import TickAttribBidAsk, TickAttribLast
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

from core.event_bus import EventBus
from ibkr.ibkr_events import (
    build_dom_delta_from_l2,
    build_from_ib_l1_tick,
    build_from_ib_tick_by_tick_all_last,
    build_from_ib_tick_by_tick_bid_ask,
)

log = logging.getLogger(__name__)


class IBKRConnector(EWrapper, EClient):
    """
    Thin IBKR API wrapper that publishes normalized MarketEvents to the EventBus.

    Fallback order:
    1) Tick-by-tick (bid/ask + all last)
    2) Level 1 market data (reqMktData)
    DOM depth is always requested for book deltas.
    """

    def __init__(
        self,
        event_bus: EventBus,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        symbol: str = "XAUUSD",
    ) -> None:
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        self.bus = event_bus
        self.symbol = symbol
        self.tick_by_tick_supported = True
        self.connected_ok = False

        log.info("[IBKR] Connecting to IB Gateway %s:%s (client_id=%s)...", host, port, client_id)
        self.connect(host, port, client_id)

        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

        # Allow connection to establish before subscribing
        time.sleep(1.0)
        self._subscribe_all()

    # ------------------------------------------------------------
    # CONTRACT
    # ------------------------------------------------------------

    def _contract(self) -> Contract:
        contract = Contract()
        contract.symbol = self.symbol
        contract.secType = "CASH"
        contract.exchange = "IDEALPRO"
        contract.currency = "USD"
        return contract

    # ------------------------------------------------------------
    # SUBSCRIPTIONS
    # ------------------------------------------------------------

    def _subscribe_all(self) -> None:
        if not self.isConnected():
            log.warning("[IBKR] Not connected; skipping subscriptions.")
            return

        self.connected_ok = True
        contract = self._contract()

        # 1) Tick-by-tick (preferred)
        try:
            log.info("[IBKR] Subscribing tick-by-tick (BidAsk + AllLast)...")
            self.reqTickByTickData(1001, contract, "BidAsk", 0, True)
            self.reqTickByTickData(1002, contract, "AllLast", 0, True)
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("[IBKR] Tick-by-tick subscription failed: %s", exc)
            self.tick_by_tick_supported = False

        # 2) DOM (always)
        try:
            self.reqMktDepth(2001, contract, 10, False, [])
            log.info("[IBKR] Subscribed DOM depth.")
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("[IBKR] DOM subscription error: %s", exc)

        # 3) Fallback to Level 1 if tick-by-tick failed
        if not self.tick_by_tick_supported:
            log.info("[IBKR] Switching to Level 1 mode (reqMktData).")
            self.reqMktData(3001, contract, "", False, False, [])

    # ------------------------------------------------------------
    # TICK-BY-TICK CALLBACKS
    # ------------------------------------------------------------

    def tickByTickBidAsk(
        self,
        reqId: int,
        time: float,
        bidPrice: float,
        askPrice: float,
        bidSize: float,
        askSize: float,
        attrib: TickAttribBidAsk,
    ) -> None:
        if not self.tick_by_tick_supported:
            return
        evt = build_from_ib_tick_by_tick_bid_ask(
            symbol=self.symbol,
            time=time,
            bid_price=bidPrice,
            ask_price=askPrice,
            bid_size=bidSize,
            ask_size=askSize,
            tick_attribs=attrib,
        )
        self.bus.publish(evt)

    def tickByTickAllLast(
        self,
        reqId: int,
        tickType: int,
        time: float,
        price: float,
        size: float,
        attrib: TickAttribLast,
        exchange: Optional[str],
        specialConditions: Optional[str],
    ) -> None:
        if not self.tick_by_tick_supported:
            return
        evt = build_from_ib_tick_by_tick_all_last(
            symbol=self.symbol,
            time=time,
            price=price,
            size=size,
            tick_attrib_last=attrib,
            exchange=exchange,
            special_conditions=specialConditions,
        )
        self.bus.publish(evt)

    # ------------------------------------------------------------
    # LEVEL 1 FALLBACK CALLBACKS
    # ------------------------------------------------------------

    def tickPrice(self, reqId: int, tickType: int, price: float, attrib) -> None:  # type: ignore[override]
        if self.tick_by_tick_supported:
            return

        evt = build_from_ib_l1_tick(
            symbol=self.symbol,
            tick_type=tickType,
            price=price,
        )
        self.bus.publish(evt)

    def tickSize(self, reqId: int, tickType: int, size: float) -> None:  # type: ignore[override]
        if self.tick_by_tick_supported:
            return
        # Size-only updates are ignored in fallback mode; they require price context.

    # ------------------------------------------------------------
    # DOM CALLBACK
    # ------------------------------------------------------------

    def updateMktDepthL2(
        self,
        reqId: int,
        position: int,
        marketMaker: str,
        operation: int,
        side: int,
        price: float,
        size: float,
        isSmartDepth: bool,
    ) -> None:
        evt = build_dom_delta_from_l2(
            symbol=self.symbol,
            side=side,
            price=price,
            size=size,
            operation=operation,
            position=position,
            market_maker=marketMaker,
            time=None,
            is_smart_depth=isSmartDepth,
        )
        self.bus.publish(evt)

    # ------------------------------------------------------------
    # CONNECTION EVENTS
    # ------------------------------------------------------------

    def nextValidId(self, orderId: int) -> None:
        log.info("[IBKR] API connection established.")

    def connectionClosed(self) -> None:
        log.warning("[IBKR] Connection closed by IBKR.")
        self.connected_ok = False

    # ------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------

    def stop(self, timeout: float = 1.0) -> None:
        """
        Gracefully stop the connector and its worker thread.
        """
        try:
            self.disconnect()
        finally:
            if self._thread.is_alive():
                self._thread.join(timeout=timeout)
