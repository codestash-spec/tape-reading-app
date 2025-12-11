import time

from core.event_bus import EventBus
from providers.provider_manager import ProviderManager


def test_provider_switching_integrity():
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"], "dom_depth": 10, "market_symbol": "ES"})
    for _ in range(2):
        for name in ("SIM", "IBKR", "BINANCE", "CME", "OKX"):
            mgr.start(name)
            time.sleep(0.05)
    mgr.stop()
    bus.stop()
