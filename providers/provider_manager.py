from __future__ import annotations

import gc
import threading
import logging
import time
from typing import Any, Dict

from core.event_bus import EventBus
from providers.provider_base import ProviderBase
from providers.ibkr_provider import IBKRProvider
from providers.cme_provider import CMEProvider
from providers.binance_provider import BinanceProvider
from providers.okx_provider import OKXProvider
from providers.sim_provider import SimProvider
from core.instrument_detector import detect_instrument


class ProviderManager:
    def __init__(self, event_bus: EventBus, settings: Dict[str, Any]) -> None:
        self.bus = event_bus
        self.settings = settings or {}
        symbol = settings.get("market_symbol") or (settings.get("symbols") or ["XAUUSD"])[0]
        self.providers: Dict[str, ProviderBase] = {
            "SIM": SimProvider(event_bus, settings, symbol),
            "IBKR": IBKRProvider(event_bus, settings, symbol),
            "CME": CMEProvider(event_bus, settings, symbol),
            "BINANCE": BinanceProvider(event_bus, settings, symbol),
            "OKX": OKXProvider(event_bus, settings, symbol),
        }
        self.active_name: str | None = None
        self.active_provider: ProviderBase | None = None
        self.log = logging.getLogger(__name__)
        self.capabilities: Dict[str, Any] = {}
        self.audit_mode = bool(settings.get("ui", {}).get("audit_mode", False))

    def start(self, name: str) -> None:
        if name not in self.providers:
            raise ValueError(f"Unknown provider {name}")
        threads_before = len(threading.enumerate())
        callbacks_before = self.bus.count_subscribers()
        if self.active_provider:
            self.log.info("[ProviderManager] Stopping provider %s...", self.active_name)
            self.active_provider.stop()
            self.active_provider = None
            self.active_name = None
            time.sleep(0.2)
            gc.collect()
        self.log.info("[ProviderManager] Starting provider: %s", name)
        self.active_name = name
        self.active_provider = self.providers[name]
        self.active_provider.start()
        self.log.info("[ProviderManager] Provider %s started", name)
        self.capabilities = {"depth_hint": self.settings.get("ui", {}).get("dom_depth", 20), "instrument_type": None}
        if self.audit_mode:
            self.log.info("[Audit][ProviderStart] provider=%s", name)
        self.bus.allowed_sources = {name}
        self._assert_provider_dead(name, threads_before, callbacks_before)

    def stop(self) -> None:
        if self.active_provider:
            self.log.info("[ProviderManager] Stopping provider %s...", self.active_name)
            self.active_provider.stop()
            if self.audit_mode:
                self.log.info("[Audit][ProviderStop] provider=%s", self.active_name)
        self.bus.allowed_sources = None
        self.active_provider = None
        self.active_name = None
        self.log.info("[ProviderManager] Provider stopped.")

    def switch(self, name: str) -> None:
        self.start(name)

    def auto_start(self) -> Dict[str, Any]:
        symbol = self.settings.get("market_symbol") or (self.settings.get("symbols") or ["XAUUSD"])[0]
        info = detect_instrument(symbol)
        self.log.info(
            "[AutoDetect] symbol=%s type=%s provider=%s execution_provider=%s",
            symbol,
            info["instrument_type"],
            info["market_provider"],
            info["execution_provider"],
        )
        self.start(info["market_provider"])
        self.capabilities = {"depth_hint": self.settings.get("ui", {}).get("dom_depth", 20), "instrument_type": info["instrument_type"]}
        return info

    def _assert_provider_dead(self, name: str, threads_before: int, callbacks_before: int) -> None:
        threads_after = len(threading.enumerate())
        callbacks_after = self.bus.count_subscribers()
        if self.audit_mode:
            self.log.info("[Audit][ThreadsBefore] %s", threads_before)
            self.log.info("[Audit][ThreadsAfter] %s", threads_after)
            self.log.info("[Audit][ActiveCallbacks] %s", callbacks_after)
        if threads_after > threads_before + 2 or callbacks_after > callbacks_before + 2:
            self.log.warning("[Audit][LeakDetected] provider %s may still be alive", name)
