from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import List

from PySide6 import QtCore, QtGui, QtWidgets

from core.config import load_settings
from core.event_bus import EventBus
from core.logging import configure_logging
from engines.microstructure.engine import MicrostructureEngine
from engines.liquidity_map.engine import LiquidityMapEngine
from engines.volume_profile.engine import VolumeProfileEngine
from engines.volatility.engine import VolatilityEngine
from engines.regime.engine import RegimeEngine
from engines.detectors.spoofing_detector import SpoofingDetector
from engines.detectors.iceberg_detector import IcebergDetector
from engines.detectors.large_trade_detector import LargeTradeDetector
from models.market_event import MarketEvent
from models.order import OrderRequest, OrderSide, OrderType
from risk.engine import RiskEngine
from execution.adapters.sim import SimAdapter
from execution.router import ExecutionRouter
from strategy.orchestrator import StrategyOrchestrator
from providers.provider_manager import ProviderManager
from ui.event_bridge import EventBridge
from ui.main_window import InstitutionalMainWindow


def build_order_from_signal(signal_evt: MarketEvent, default_qty: float = 1.0) -> OrderRequest:
    payload = signal_evt.payload
    direction = payload.get("direction", "flat")
    side = OrderSide.BUY if direction == "buy" else OrderSide.SELL
    limit_price = payload.get("features", {}).get("mid") or payload.get("price") or payload.get("last")
    qty = float(payload.get("metadata", {}).get("qty", default_qty))
    return OrderRequest(
        order_id=uuid.uuid4().hex,
        symbol=os.getenv("EXEC_SYMBOL", signal_evt.symbol),
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
    pm_settings = {
        "symbols": symbols,
        "market_symbol": settings.market_symbol,
        "execution_symbol": settings.execution_symbol,
        "execution_provider": settings.execution_provider,
        "ui": settings.ui,
        "instrument_type": None,
    }
    provider_manager = ProviderManager(bus, pm_settings)
    autodetect = provider_manager.auto_start()

    # Engines and strategy
    micro = MicrostructureEngine(bus, symbols)
    micro.start()
    # Institutional engines
    liq_map_engine = LiquidityMapEngine(bus)
    vol_profile_engine = VolumeProfileEngine(bus)
    vol_engine = VolatilityEngine(bus)
    regime_engine = RegimeEngine(bus)
    spoof_detector = SpoofingDetector(bus)
    iceberg_detector = IcebergDetector(bus)
    large_trade_detector = LargeTradeDetector(bus)

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
        provider_manager=provider_manager,
        event_bus=bus,
        pm_settings=pm_settings,
    )
    window.resize(1400, 900)
    window.show()
    splash.finish(window)

    ret = app.exec()

    # shutdown
    bridge.stop()
    provider_manager.stop()
    bus.stop()
    log.info("UI shutdown complete")
    return ret


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
