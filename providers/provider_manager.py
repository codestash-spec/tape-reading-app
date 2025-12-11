from __future__ import annotations

from typing import Any, Dict

from core.event_bus import EventBus
from providers.provider_base import ProviderBase
from providers.ibkr_provider import IBKRProvider
from providers.cme_provider import CMEProvider
from providers.binance_provider import BinanceProvider
from providers.okx_provider import OKXProvider
from providers.sim_provider import SimProvider


class ProviderManager:
    def __init__(self, event_bus: EventBus, settings: Dict[str, Any]) -> None:
        self.bus = event_bus
        self.settings = settings or {}
        symbol = (settings.get("symbols") or ["XAUUSD"])[0]
        self.providers: Dict[str, ProviderBase] = {
            "SIM": SimProvider(event_bus, settings, symbol),
            "IBKR": IBKRProvider(event_bus, settings, symbol),
            "CME": CMEProvider(event_bus, settings, symbol),
            "BINANCE": BinanceProvider(event_bus, settings, symbol),
            "OKX": OKXProvider(event_bus, settings, symbol),
        }
        self.active_name: str | None = None
        self.active_provider: ProviderBase | None = None

    def start(self, name: str) -> None:
        if name not in self.providers:
            raise ValueError(f"Unknown provider {name}")
        if self.active_provider:
            self.active_provider.stop()
        self.active_name = name
        self.active_provider = self.providers[name]
        self.active_provider.start()

    def stop(self) -> None:
        if self.active_provider:
            self.active_provider.stop()
        self.active_provider = None
        self.active_name = None

    def switch(self, name: str) -> None:
        self.start(name)
