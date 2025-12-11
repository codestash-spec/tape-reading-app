from providers.ibkr_provider import IBKRProvider
from core.event_bus import EventBus


def test_ibkr_futures_depth_normalization():
    bus = EventBus()
    settings = {"instrument_type": "FUTURES", "ui": {"dom_depth": 10}}
    provider = IBKRProvider(bus, settings, "GCZ4")
    evt = provider.normalize_dom(
        {
            "dom": [{"price": 100.0, "bid_size": 10, "ask_size": 0}, {"price": 100.1, "bid_size": 0, "ask_size": 9}],
            "last": 100.0,
        }
    )
    assert evt.payload["ladder"]
    assert len(evt.payload["ladder"]) == 2
