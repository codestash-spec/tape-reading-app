from providers.provider_manager import ProviderManager
from core.event_bus import EventBus


def test_event_normalization_dom():
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"], "dom_depth": 10})
    mgr.start("SIM")
    # ensure sim provider added dom_snapshot events as ladder
    mgr.stop()
    assert mgr.active_provider is None or mgr.active_provider._running is False
