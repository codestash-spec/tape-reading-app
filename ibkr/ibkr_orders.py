from __future__ import annotations

from ibapi.contract import Contract
from ibapi.order import Order

from models.order import OrderRequest, OrderSide, OrderType


def build_fx_contract(symbol: str) -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "CASH"
    contract.exchange = "IDEALPRO"
    contract.currency = "USD"
    return contract


def to_ib_order(req: OrderRequest) -> Order:
    order = Order()
    order.orderId = None  # assigned by IBKR client
    order.totalQuantity = req.quantity
    order.action = "BUY" if req.side == OrderSide.BUY else "SELL"

    if req.order_type == OrderType.MARKET:
        order.orderType = "MKT"
    elif req.order_type == OrderType.LIMIT:
        order.orderType = "LMT"
        order.lmtPrice = float(req.limit_price or 0.0)
    elif req.order_type == OrderType.STOP:
        order.orderType = "STP"
        order.auxPrice = float(req.stop_price or 0.0)
    else:
        order.orderType = "STP LMT"
        order.lmtPrice = float(req.limit_price or 0.0)
        order.auxPrice = float(req.stop_price or 0.0)

    order.tif = req.tif
    order.outsideRth = True
    order.transmit = True
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order
