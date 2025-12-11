from core.event_bus import EventBus
from providers.provider_manager import ProviderManager


def test_settings_provider_switch():
    bus = EventBus()
    mgr = ProviderManager(bus, {"symbols": ["ES"]})
    mgr.start("SIM")
    assert mgr.active_name == "SIM"
    mgr.switch("IBKR")
    assert mgr.active_name == "IBKR"
    mgr.stop()
