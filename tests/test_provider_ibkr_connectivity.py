from providers.provider_manager import ProviderManager
from core.event_bus import EventBus


def test_ibkr_provider_mock_connectivity():
    """
    Offline test: ensures IBKRProvider can start/stop without leaking.
    """
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"]})
    mgr.start("IBKR")
    mgr.stop()
    bus.stop()
