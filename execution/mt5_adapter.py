from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from core.event_bus import EventBus
from models.market_event import MarketEvent
from models.order import OrderEvent, OrderRequest, OrderStatus, OrderSide

log = logging.getLogger(__name__)


class MT5ExecutionAdapter:
    """
    Thin MT5 execution adapter for MARKET orders (BTCUSDT only, configurable symbol).
    Supports dry_run to avoid real sends during testing.
    """

    def __init__(self, bus: EventBus, symbol_map: Dict[str, str], default_volume: float = 0.01, dry_run: bool = True) -> None:
        self.bus = bus
        self.symbol_map = symbol_map or {}
        self.default_volume = default_volume
        self.dry_run = dry_run
        self.mt5 = None
        self._connected = False
        self._import_mt5()

    def _import_mt5(self) -> None:
        try:
            import MetaTrader5 as mt5  # type: ignore

            self.mt5 = mt5
        except Exception as exc:
            log.error("[MT5] MetaTrader5 module not available: %s", exc)
            self.mt5 = None

    def connect(self) -> bool:
        if not self.mt5:
            return False
        if self._connected:
            return True
        ok = self.mt5.initialize()
        if not ok:
            err = self.mt5.last_error()
            log.error("[MT5] initialize failed: %s", err)
            return False
        info = self.mt5.account_info()
        log.info("[MT5] initialize OK, account=%s", getattr(info, "login", "?"))
        self._connected = True
        return True

    def disconnect(self) -> None:
        if self.mt5 and self._connected:
            try:
                self.mt5.shutdown()
            except Exception:
                pass
        self._connected = False

    def is_connected(self) -> bool:
        return bool(self._connected)

    def send_order(self, order: OrderRequest) -> None:
        symbol = self.symbol_map.get(order.symbol, order.symbol)
        side = order.side
        vol = self.default_volume or order.quantity
        if not self.mt5:
            log.error("[MT5] send_order called but mt5 module missing")
            return
        if not self.connect():
            log.error("[MT5] unable to connect, dropping order %s", order.order_id)
            return

        ack = OrderEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            status=OrderStatus.ACK,
            timestamp=datetime.now(timezone.utc),
            filled_qty=0.0,
            raw={"adapter": "MT5"},
        )
        self._publish(ack, source="execution_mt5")

        if self.dry_run:
            log.warning("[Execution] DRY RUN – MT5 order not actually sent %s %s @%s vol=%s", side, symbol, order.limit_price, vol)
            return

        mt5_side = self.mt5.ORDER_TYPE_BUY if side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": vol,
            "type": mt5_side,
            "price": order.limit_price or order.stop_price or 0.0,
            "deviation": 20,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
            "comment": "ibkr_bot",
        }
        try:
            result = self.mt5.order_send(request)
            if result is None:
                log.error("[MT5] order_send returned None for %s", order.order_id)
                return
            if result.retcode != self.mt5.TRADE_RETCODE_DONE:
                log.error("[MT5] order_send failed retcode=%s comment=%s", result.retcode, result.comment)
                return
            fill = OrderEvent(
                order_id=order.order_id,
                symbol=order.symbol,
                status=OrderStatus.FILL,
                timestamp=datetime.now(timezone.utc),
                filled_qty=order.quantity,
                avg_price=result.price,
                raw={"retcode": result.retcode, "deal": result.deal, "order": result.order},
            )
            self._publish(fill, source="execution_mt5")
        except Exception as exc:
            log.exception("[MT5] order_send exception: %s", exc)

    def cancel_order(self, order_id: str) -> None:
        log.info("[MT5] cancel stub for order %s", order_id)

    def _publish(self, evt: OrderEvent, source: Optional[str] = None) -> None:
        event = MarketEvent(
            event_type="order_event",
            timestamp=evt.timestamp,
            source=source or "execution_mt5",
            symbol=evt.symbol,
            payload=evt.model_dump(),
        )
        self.bus.publish(event)
