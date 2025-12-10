from __future__ import annotations

import argparse
import os
import signal
import sys
import time
import uuid
from typing import List

from core.config import load_settings
from core.event_bus import EventBus
from core.logging import configure_logging
from engines.dom import DOMEngine
from engines.delta import DeltaEngine
from engines.footprint import FootprintEngine
from engines.strategy import MicroPriceMomentumStrategy
from engines.tape import TapeEngine
from execution.adapters.ibkr import IBKRAdapter
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from ibkr.ibkr_connector import IBKRConnector
from models.market_event import MarketEvent
from models.order import OrderRequest, OrderSide, OrderType
from models.risk import RiskDecision
from risk.engine import RiskEngine


def build_order_from_signal(signal_evt: MarketEvent, default_qty: float = 1.0) -> OrderRequest:
    payload = signal_evt.payload
    direction = payload.get("direction", "flat")
    side = OrderSide.BUY if direction == "buy" else OrderSide.SELL
    limit_price = payload.get("features", {}).get("mid") or payload.get("price") or payload.get("last")
    qty = float(payload.get("metadata", {}).get("qty", default_qty))
    return OrderRequest(
        order_id=uuid.uuid4().hex,
        symbol=signal_evt.symbol,
        side=side,
        quantity=qty,
        order_type=OrderType.LIMIT if limit_price else OrderType.MARKET,
        limit_price=limit_price,
    )


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="BOTS INSTITUCIONAIS – Fase III live runner")
    parser.add_argument("--profile", default=os.getenv("PROFILE", "dev"))
    parser.add_argument("--mode", choices=["sim", "ibkr"], default=None, help="Execution mode")
    parser.add_argument("--symbol", action="append", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args(argv)

    os.environ["PROFILE"] = args.profile
    settings = load_settings()
    mode = args.mode or settings.execution.get("mode", "sim")
    symbols = args.symbol or settings.symbols

    configure_logging(settings.telemetry.get("log_level", "INFO"))
    bus = EventBus()

    # Engines
    dom = DOMEngine(bus)
    delta = DeltaEngine(bus)
    tape = TapeEngine(bus)
    footprint = FootprintEngine(bus)
    strategy = MicroPriceMomentumStrategy(bus, symbols, threshold=0.0)
    strategy.on_start()

    # Risk and execution
    risk_engine = RiskEngine(settings.risk_limits)
    adapter = SimAdapter(bus) if mode == "sim" else IBKRAdapter(bus, settings.ibkr_host, settings.ibkr_port, settings.ibkr_client_id)
    router = ExecutionRouter(bus, adapter)

    # Signal -> order pipeline
    def on_signal(evt: MarketEvent) -> None:
        order = build_order_from_signal(evt, default_qty=settings.execution.get("default_qty", 1.0))
        decision = risk_engine.evaluate(order, account_ctx={})
        bus.publish(
            MarketEvent(
                event_type="risk_decision",
                timestamp=decision.timestamp,
                source="risk",
                symbol=order.symbol,
                payload=decision.model_dump(),
            )
        )
        if decision.approved:
            router.submit(order)

    bus.subscribe("signal", on_signal)

    # Market data source
    connector = None
    if mode == "ibkr":
        connector = IBKRConnector(
            event_bus=bus,
            host=args.host or settings.ibkr_host,
            port=args.port or settings.ibkr_port,
            client_id=settings.ibkr_client_id,
            symbol=symbols[0],
        )

    stop = False

    def handle_sigint(sig, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    while not stop:
        time.sleep(0.5)

    if connector:
        connector.stop()
    bus.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
