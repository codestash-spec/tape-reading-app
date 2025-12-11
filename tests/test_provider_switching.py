from core.event_bus import EventBus
from providers.provider_manager import ProviderManager


def test_provider_switching_no_crash():
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"], "dom_depth": 10})
    mgr.start("IBKR")
    mgr.start("BINANCE")
    mgr.start("CME")
    mgr.start("OKX")
    mgr.stop()
    bus.stop()
    # if we reach here without exceptions, the switch was clean
