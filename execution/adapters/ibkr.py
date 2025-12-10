from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from core.event_bus import EventBus
from ibkr.ibkr_orders import build_fx_contract, to_ib_order
from models.order import OrderEvent, OrderRequest, OrderStatus
from models.market_event import MarketEvent

log = logging.getLogger(__name__)


class IBKRAdapter(EWrapper, EClient):
    """
    Stubbed IBKR order adapter. Maps OrderRequest into IBKR orders.
    """

    def __init__(self, bus: EventBus, host: str, port: int, client_id: int) -> None:
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.bus = bus
        self._order_map: dict[int, str] = {}
        self._order_symbol: dict[int, str] = {}
        self.connect(host, port, client_id)
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def send(self, order: OrderRequest) -> None:
        ib_order = to_ib_order(order)
        ib_contract = build_fx_contract(order.symbol)
        ib_id = self.nextOrderId()
        self._order_map[ib_id] = order.order_id
        self._order_symbol[ib_id] = order.symbol
        self.placeOrder(ib_id, ib_contract, ib_order)
        ack = OrderEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            status=OrderStatus.ACK,
            timestamp=datetime.now(timezone.utc),
            filled_qty=0.0,
            raw={"ib_id": ib_id},
        )
        self._publish(ack)

    def cancel(self, order_id: str) -> None:
        for ib_id, oid in list(self._order_map.items()):
            if oid == order_id:
                self.cancelOrder(ib_id)
                evt = OrderEvent(
                    order_id=order_id,
                    symbol="",
                    status=OrderStatus.CANCEL,
                    timestamp=datetime.now(timezone.utc),
                    raw={"ib_id": ib_id},
                )
                self._publish(evt)

    def replace(self, order_id: str, new_order: OrderRequest) -> None:
        # Simplified: cancel then send
        self.cancel(order_id)
        self.send(new_order)

    # ------------------------------------------------------------
    # IBKR CALLBACKS
    # ------------------------------------------------------------
    def nextValidId(self, orderId: int) -> None:  # pragma: no cover - IBKR
        self._next_id = orderId

    def nextOrderId(self) -> int:
        next_id = getattr(self, "_next_id", 10000)
        self._next_id = next_id + 1
        return next_id

    def openOrder(self, orderId, contract, order, state):  # pragma: no cover - IBKR
        pass

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):  # pragma: no cover - IBKR
        oid = self._order_map.get(orderId, str(orderId))
        evt = OrderEvent(
            order_id=oid,
            symbol=self._order_symbol.get(orderId, ""),
            status=OrderStatus.PARTIAL if status not in ("Cancelled", "Filled") else OrderStatus.FILL,
            timestamp=datetime.now(timezone.utc),
            filled_qty=filled,
            avg_price=avgFillPrice,
            raw={"status": status, "remaining": remaining, "why": whyHeld},
        )
        self._publish(evt)

    # ------------------------------------------------------------
    def _publish(self, evt: OrderEvent) -> None:
        market_evt = evt.model_dump()
        self.bus.publish(
            MarketEvent(
                event_type="order_event",
                timestamp=evt.timestamp,
                source="execution",
                symbol=evt.symbol,
                payload=market_evt,
            )
        )
