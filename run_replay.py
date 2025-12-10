from __future__ import annotations

import argparse
import sys

from core.config import load_settings
from core.event_bus import EventBus
from core.logging import configure_logging
from engines.dom import DOMEngine
from engines.delta import DeltaEngine
from engines.footprint import FootprintEngine
from engines.strategy import MicroPriceMomentumStrategy
from engines.tape import TapeEngine
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from models.market_event import MarketEvent
from models.order import OrderRequest, OrderSide, OrderType
from providers.historical_loader import HistoricalLoader
from risk.engine import RiskEngine


def build_order_from_signal(signal_evt: MarketEvent, default_qty: float = 1.0) -> OrderRequest:
    payload = signal_evt.payload
    direction = payload.get("direction", "flat")
    side = OrderSide.BUY if direction == "buy" else OrderSide.SELL
    limit_price = payload.get("features", {}).get("mid") or payload.get("price") or payload.get("last")
    qty = float(payload.get("metadata", {}).get("qty", default_qty))
    return OrderRequest(
        order_id=f"replay-{signal_evt.timestamp.timestamp()}",
        symbol=signal_evt.symbol,
        side=side,
        quantity=qty,
        order_type=OrderType.LIMIT if limit_price else OrderType.MARKET,
        limit_price=limit_price,
    )


def main(argv):
    parser = argparse.ArgumentParser(description="Replay historical events through the pipeline.")
    parser.add_argument("--file", required=True, help="Path to JSON/CSV historical events")
    parser.add_argument("--speed", type=float, default=None)
    args = parser.parse_args(argv)

    settings = load_settings()
    configure_logging(settings.telemetry.get("log_level", "INFO"))
    bus = EventBus()

    DOMEngine(bus)
    DeltaEngine(bus)
    TapeEngine(bus)
    FootprintEngine(bus)
    strategy = MicroPriceMomentumStrategy(bus, settings.symbols, threshold=0.0)
    strategy.on_start()

    risk_engine = RiskEngine(settings.risk_limits)
    adapter = SimAdapter(bus)
    router = ExecutionRouter(bus, adapter)

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

    loader = HistoricalLoader(bus)
    if args.file.lower().endswith(".json"):
        loader.load_json(args.file)
    else:
        loader.load_csv(args.file)
    loader.replay(speed=args.speed or settings.replay.get("speed", 1.0))
    bus.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
