import threading
import time
from typing import Optional

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

from ibapi.TickAttribBidAsk import TickAttribBidAsk
from ibapi.TickAttribLast import TickAttribLast

from core.event_bus import EventBus
from ibkr.ibkr_events import (
    build_from_ib_tick_by_tick_bid_ask,
    build_from_ib_tick_by_tick_all_last,
    build_from_ib_l1_tick,
    build_dom_delta_from_l2,
)


class IBKRConnector(EWrapper, EClient):

    def __init__(
        self,
        event_bus: EventBus,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 1,
        symbol: str = "XAUUSD"
    ):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)

        self.bus = event_bus
        self.symbol = symbol

        self.tick_by_tick_supported = True   # vamos testar
        self.connected_ok = False

        print(f"[IBKR] Connecting to IB Gateway {host}:{port} (client_id={client_id})...")
        self.connect(host, port, client_id)

        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

        time.sleep(1.0)

        self._subscribe_all()

    # ------------------------------------------------------------
    # CONTRACT
    # ------------------------------------------------------------

    def _contract(self) -> Contract:
        c = Contract()
        c.symbol = self.symbol
        c.secType = "CASH"
        c.exchange = "IDEALPRO"
        c.currency = "USD"
        return c

    # ------------------------------------------------------------
    # SUBSCRIPTIONS
    # ------------------------------------------------------------

    def _subscribe_all(self):
        if not self.isConnected():
            print("[IBKR] Not connected.")
            return

        self.connected_ok = True
        contract = self._contract()

        # 1) Tentamos tick-by-tick moderno
        try:
            print("[IBKR] Subscribing tick-by-tick (BidAsk + AllLast)...")
            self.reqTickByTickData(1001, contract, "BidAsk", 0, True)
            self.reqTickByTickData(1002, contract, "AllLast", 0, True)
        except Exception as e:
            print(f"[IBKR] Tick-by-tick subscription failed: {e}")
            self.tick_by_tick_supported = False

        # 2) DOM — funciona mesmo sem market data real
        try:
            self.reqMktDepth(2001, contract, 10, False, [])
            print("[IBKR] Subscribed DOM.")
        except Exception as e:
            print(f"[IBKR] DOM subscription error: {e}")

        # 3) Se tick-by-tick falhar → fallback automático para L1
        if not self.tick_by_tick_supported:
            print("[IBKR] Switching to Level 1 mode (reqMktData).")
            self.reqMktData(3001, contract, "", False, False, [])

    # ------------------------------------------------------------
    # TICK-BY-TICK CALLBACKS
    # ------------------------------------------------------------

    def tickByTickBidAsk(
        self, reqId, time, bidPrice, askPrice, bidSize, askSize, attrib: TickAttribBidAsk
    ):
        if not self.tick_by_tick_supported:
            return
        evt = build_from_ib_tick_by_tick_bid_ask(
            symbol=self.symbol,
            time=time,
            bid=bidPrice,
            ask=askPrice,
            bid_size=bidSize,
            ask_size=askSize,
        )
        self.bus.publish("tick", evt)

    def tickByTickAllLast(
        self, reqId, time, price, size, attrib: TickAttribLast, tickType
    ):
        if not self.tick_by_tick_supported:
            return
        evt = build_from_ib_tick_by_tick_all_last(
            symbol=self.symbol,
            time=time,
            price=price,
            size=size,
        )
        self.bus.publish("trade", evt)

    # ------------------------------------------------------------
    # LEVEL 1 FALLBACK CALLBACKS
    # ------------------------------------------------------------

    def tickPrice(self, reqId, tickType, price, attrib):
        if self.tick_by_tick_supported:
            return  # ignoramos L1 quando tick-by-tick funciona

        evt = build_from_ib_l1_tick(
            symbol=self.symbol,
            tick_type=tickType,
            price=price
        )
        self.bus.publish("tick", evt)

    def tickSize(self, reqId, tickType, size):
        if self.tick_by_tick_supported:
            return
        # opcional: podemos juntar size ao tick

    # ------------------------------------------------------------
    # DOM CALLBACK
    # ------------------------------------------------------------

    def updateMktDepthL2(
        self, reqId, position, marketMaker, operation, side, price, size, isSmartDepth
    ):
        evt = build_dom_delta_from_l2(
            symbol=self.symbol,
            side=side,
            price=price,
            size=size,
            operation=operation,
            position=position,
        )
        self.bus.publish("dom", evt)

    # ------------------------------------------------------------
    # CONNECTION EVENTS
    # ------------------------------------------------------------

    def nextValidId(self, orderId):
        print("[IBKR] API connection established.")

    def connectionClosed(self):
        print("[IBKR] WARNING: Connection closed by IBKR.")
        self.connected_ok = False
