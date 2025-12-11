from __future__ import annotations

import argparse
import logging
import os
import random
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from core.config import load_settings
from core.event_bus import EventBus
from core.logging import configure_logging
from engines.microstructure.engine import MicrostructureEngine
from models.market_event import MarketEvent
from models.order import OrderRequest, OrderSide, OrderType
from risk.engine import RiskEngine
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from strategy.orchestrator import StrategyOrchestrator
from ui.event_bridge import EventBridge
from ui.main_window import InstitutionalMainWindow


class SyntheticFeed(threading.Thread):
    """
    Generates synthetic DOM/trade events to keep the UI alive in simulation mode.
    """

    def __init__(self, bus: EventBus, symbols: List[str], interval: float = 0.25) -> None:
        super().__init__(daemon=True)
        self.bus = bus
        self.symbols = symbols
        self.interval = interval
        self._running = True

    def run(self) -> None:
        while self._running:
            sym = random.choice(self.symbols)
            mid = 100 + random.random()
            bid = mid - 0.05
            ask = mid + 0.05
            dom_evt = MarketEvent(
                event_type="dom_snapshot",
                timestamp=datetime.now(timezone.utc),
                source="synthetic",
                symbol=sym,
                payload={
                    "bid": bid,
                    "ask": ask,
                    "bid_size": random.randint(50, 200),
                    "ask_size": random.randint(50, 200),
                    "ladder": {
                        f"{bid:.2f}": {"bid": random.randint(50, 200), "ask": 0},
                        f"{ask:.2f}": {"bid": 0, "ask": random.randint(50, 200)},
                    },
                },
            )
            trade_evt = MarketEvent(
                event_type="trade",
                timestamp=datetime.now(timezone.utc),
                source="synthetic",
                symbol=sym,
                payload={
                    "price": mid,
                    "size": random.randint(1, 20),
                    "side": random.choice(["buy", "sell"]),
                },
            )
            self.bus.publish(dom_evt)
            self.bus.publish(trade_evt)
            time.sleep(self.interval)

    def stop(self) -> None:
        self._running = False


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


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Institutional UI for Bots Institucionais")
    parser.add_argument("--profile", default=os.getenv("PROFILE", "dev"))
    parser.add_argument("--mode", choices=["sim", "ibkr", "replay"], default=None)
    args = parser.parse_args(argv)

    os.environ["PROFILE"] = args.profile
    settings = load_settings()
    mode = args.mode or settings.ui.get("mode", "sim")

    configure_logging(settings.log_level)
    log = logging.getLogger(__name__)

    bus = EventBus()
    symbols = settings.symbols

    # Engines and strategy
    micro = MicrostructureEngine(bus, symbols)
    micro.start()
    strategist = StrategyOrchestrator(bus, symbols)
    strategist.start()

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

    # Synthetic feed for UI simulation
    synth = SyntheticFeed(bus, symbols)
    synth.start()

    # Qt Application
    app = QtWidgets.QApplication(sys.argv)
    splash = QtWidgets.QSplashScreen(QtGui.QPixmap(400, 300))
    splash.showMessage("Loading Institutional UI...", QtCore.Qt.AlignCenter)  # type: ignore
    splash.show()
    app.processEvents()
    bridge = EventBridge(bus)
    bridge.start()

    window = InstitutionalMainWindow(
        bridge,
        theme_mode=settings.ui.get("theme", "dark"),
        mode=mode,
        on_submit_order=router.submit,
        on_cancel_order=router.cancel,
    )
    window.resize(1400, 900)
    window.show()
    splash.finish(window)

    ret = app.exec()

    # shutdown
    bridge.stop()
    synth.stop()
    synth.join(timeout=1.0)
    bus.stop()
    log.info("UI shutdown complete")
    return ret


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
