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
from execution.mt5_adapter import MT5ExecutionAdapter
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

    exec_mode = settings.execution.get("mode", "sim").upper()

    def build_adapter():
        if exec_mode == "MT5":
            mt5_symbol = settings.execution.get("mt5_symbol_btc", "BTCUSD")
            mt5_vol = float(settings.execution.get("mt5_volume_btc", 0.01))
            dry_run = bool(settings.execution.get("dry_run", True))
            return MT5ExecutionAdapter(bus, {"BTCUSDT": mt5_symbol, settings.market_symbol: mt5_symbol}, mt5_vol, dry_run), exec_mode
        return SimAdapter(bus), "SIM"

    def build_engines(sym_list: list[str]):
        micro = MicrostructureEngine(bus, sym_list)
        micro.start()
        ohlc = OHLCEngine(bus, timeframe_seconds=settings.ui.get("ohlc_seconds", 1))
        liq_map_engine = LiquidityMapEngine(bus)
        vol_profile_engine = VolumeProfileEngine(bus)
        vol_engine = VolatilityEngine(bus)
        regime_engine = RegimeEngine(bus)
        spoof_detector = SpoofingDetector(bus)
        iceberg_detector = IcebergDetector(bus)
        large_trade_detector = LargeTradeDetector(bus)
        simple_strategy = SimpleStrategyEngine(bus)
        strategist = StrategyOrchestrator(bus, sym_list)
        strategist.start()
        risk_engine = RiskEngine(settings.risk_limits)
        adapter, mode_adapter = build_adapter()
        router = ExecutionRouter(bus, adapter, mode=mode_adapter)

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
        log.info("[EngineReset] Rebinding engines to provider=%s", provider_manager.active_name)
        return {
            "micro": micro,
            "ohlc": ohlc,
            "liq_map_engine": liq_map_engine,
            "vol_profile_engine": vol_profile_engine,
            "vol_engine": vol_engine,
            "regime_engine": regime_engine,
            "spoof_detector": spoof_detector,
            "iceberg_detector": iceberg_detector,
            "large_trade_detector": large_trade_detector,
            "simple_strategy": simple_strategy,
            "strategist": strategist,
            "risk_engine": risk_engine,
            "adapter": adapter,
            "router": router,
            "on_signal": on_signal,
            "mode": mode_adapter,
        }

    def stop_engines(bundle):
        if not bundle:
            return
        on_sig = bundle.get("on_signal")
        if on_sig:
            bus.unsubscribe("signal", on_sig)
            bus.unsubscribe("strategy_signal", on_sig)
        for key in (
            "micro",
            "ohlc",
            "liq_map_engine",
            "vol_profile_engine",
            "vol_engine",
            "regime_engine",
            "spoof_detector",
            "iceberg_detector",
            "large_trade_detector",
            "simple_strategy",
            "strategist",
        ):
            eng = bundle.get(key)
            if eng and hasattr(eng, "stop"):
                try:
                    eng.stop()
                except Exception:
                    log.exception("Error stopping engine %s", key)

    autodetect = provider_manager.auto_start(settings.market_symbol or "BTCUSDT")
    log.info("[AutoStart] market=%s provider=%s", settings.market_symbol or "BTCUSDT", autodetect.get("market_provider"))
    log.info("[MarketWatch] No override. Keeping auto-start instrument.")
    log.info("[Provider] %s WS requested", autodetect.get("market_provider", "unknown"))

    engines = build_engines([settings.market_symbol or "BTCUSDT"])
    router = engines["router"]
    mode_adapter = engines.get("mode", "SIM")
    log.info("[Strategy] Engine ready")
    log.info("[Execution] %s execution ready", mode_adapter)

    window_ref: InstitutionalMainWindow | None = None

    def switch_symbol(symbol: str) -> None:
        nonlocal provider_manager, engines, window_ref, router
        log.info("[EngineReset] All engines stopped")
        stop_engines(engines)
        provider_manager.stop()
        cfg = dict(pm_settings)
        cfg["market_symbol"] = symbol
        cfg["symbols"] = [symbol]
        provider_manager = ProviderManager(bus, cfg)
        autodetect_local = provider_manager.auto_start(symbol)
        bus.allowed_sources = {provider_manager.active_name.lower()} if provider_manager.active_name else None
        engines = build_engines([symbol])
        router = engines["router"]
        log.info("[EngineReset] Rebinding engines to provider=%s", provider_manager.active_name)
        log.info("[AutoStart] market=%s provider=%s", symbol, autodetect_local.get("market_provider"))
        if window_ref and hasattr(window_ref, "status_widget"):
            window_ref.status_widget.conn_label.setText(f"Conn: {provider_manager.active_name}")
            window_ref.on_submit_order = router.submit
            window_ref.on_cancel_order = router.cancel
        log.info("[MarketWatch] User switch symbol -> %s", symbol)

    # Qt Application
    app = QtWidgets.QApplication(sys.argv)
    splash = QtWidgets.QSplashScreen(QtGui.QPixmap(400, 300))
    splash.showMessage("Loading Institutional UI...", QtCore.Qt.AlignCenter)  # type: ignore
    splash.show()
    app.processEvents()
    bridge = EventBridge(bus)
    bridge.start()

    router = engines["router"]
    window = InstitutionalMainWindow(
        bridge,
        theme_mode=settings.ui.get("theme", "dark"),
        mode=mode,
        on_submit_order=router.submit,
        on_cancel_order=router.cancel,
        provider_manager=provider_manager,
        event_bus=bus,
        pm_settings=pm_settings,
        on_switch_symbol=switch_symbol,
    )
    window_ref = window
    if hasattr(window, "execution_mode_label"):
        window.execution_mode_label.setText(f"Exec: {mode_adapter}")
    # attach FPS monitor label to status bar if available
    helpers.FPS_MONITOR = window.status_widget if hasattr(window, "status_widget") else None
    window.market_watch.apply_default_symbol_on_start(settings.market_symbol or "BTCUSDT", apply=False)
    log.info("[MarketWatch] Default symbol %s selected (no override)", settings.market_symbol or "BTCUSDT")
    if hasattr(window, "status_widget") and provider_manager.active_name:
        window.status_widget.conn_label.setText(f"Conn: {provider_manager.active_name}")
    window.resize(1400, 900)
    window.show()
    splash.finish(window)
    log.info("[UI] All core panels online")
    log.info("[Chart] Renderer active (line/candles)")

    ret = app.exec()

    # shutdown
    bridge.stop()
    stop_engines(engines)
    provider_manager.stop()
    bus.stop()
    log.info("UI shutdown complete")
    return ret


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
