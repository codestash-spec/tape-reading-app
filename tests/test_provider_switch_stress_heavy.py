import pytest

from core.event_bus import EventBus
from providers.provider_manager import ProviderManager


@pytest.mark.timeout(10)
def test_provider_switch_stress_heavy():
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"], "dom_depth": 10})
    providers = ["SIM", "BINANCE", "OKX", "IBKR"]
    for i in range(200):
        mgr.start(providers[i % len(providers)])
    mgr.stop()
    bus.stop()
