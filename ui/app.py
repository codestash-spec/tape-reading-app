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
from engines.ohlc.engine import OHLCEngine
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
from strategy.simple_strategy import SimpleStrategyEngine
from providers.provider_manager import ProviderManager
from ui.event_bridge import EventBridge
from ui.main_window import InstitutionalMainWindow
from ui import helpers


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
    symbols = settings.symbols or ["BTCUSDT"]
    if not settings.market_symbol:
        settings.market_symbol = "BTCUSDT"
    pm_settings = {
        "symbols": symbols,
        "market_symbol": settings.market_symbol or "BTCUSDT",
        "execution_symbol": settings.execution_symbol,
        "execution_provider": settings.execution_provider,
        "ui": settings.ui,
        "instrument_type": None,
    }
    provider_manager = ProviderManager(bus, pm_settings)
    autodetect = provider_manager.auto_start(settings.market_symbol or "BTCUSDT")
    log.info("[AutoStart] Market symbol: %s", settings.market_symbol or "BTCUSDT")
    log.info("[Provider] %s WS requested", autodetect.get("market_provider", "unknown"))

    # Engines and strategy
    micro = MicrostructureEngine(bus, symbols)
    micro.start()
    ohlc = OHLCEngine(bus, timeframe_seconds=settings.ui.get("ohlc_seconds", 1))
    # Institutional engines
    liq_map_engine = LiquidityMapEngine(bus)
    vol_profile_engine = VolumeProfileEngine(bus)
    vol_engine = VolatilityEngine(bus)
    regime_engine = RegimeEngine(bus)
    spoof_detector = SpoofingDetector(bus)
    iceberg_detector = IcebergDetector(bus)
    large_trade_detector = LargeTradeDetector(bus)
    simple_strategy = SimpleStrategyEngine(bus)

    strategist = StrategyOrchestrator(bus, symbols)
    strategist.start()
    log.info("[Strategy] Engine ready")

    risk_engine = RiskEngine(settings.risk_limits)
    adapter = SimAdapter(bus)
    router = ExecutionRouter(bus, adapter)
    log.info("[Execution] SIM execution ready")

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
    bus.subscribe("strategy_signal", on_signal)

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
    # attach FPS monitor label to status bar if available
    helpers.FPS_MONITOR = window.status_widget if hasattr(window, "status_widget") else None
    window.market_watch.apply_default_symbol_on_start(settings.market_symbol or "BTCUSDT")
    log.info("[MarketWatch] Applied default symbol %s", settings.market_symbol or "BTCUSDT")
    window.resize(1400, 900)
    window.show()
    splash.finish(window)
    log.info("[UI] All core panels online")
    log.info("[Chart] Renderer active (line/candles)")

    ret = app.exec()

    # shutdown
    bridge.stop()
    provider_manager.stop()
    bus.stop()
    log.info("UI shutdown complete")
    return ret


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
