from __future__ import annotations

import gc
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

    def start(self, name: str) -> None:
        if name not in self.providers:
            raise ValueError(f"Unknown provider {name}")
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
        self.capabilities = {"depth_hint": self.settings.get("ui", {}).get("dom_depth", 20)}

    def stop(self) -> None:
        if self.active_provider:
            self.log.info("[ProviderManager] Stopping provider %s...", self.active_name)
            self.active_provider.stop()
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
