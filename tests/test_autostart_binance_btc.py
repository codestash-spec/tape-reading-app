from providers.provider_manager import ProviderManager
from core.event_bus import EventBus
import providers.binance_provider as bp


def test_autostart_binance_btc(monkeypatch):
    started = {"binance": False}

    def fake_start(self):
        started["binance"] = True

    monkeypatch.setattr(bp.BinanceProvider, "start", fake_start)
    bus = EventBus()
    settings = {"symbols": ["BTCUSDT"], "market_symbol": "BTCUSDT", "ui": {}}
    pm = ProviderManager(bus, settings)
    pm.auto_start("BTCUSDT")
    assert started["binance"]
    assert bus.allowed_sources == {"binance"}
    bus.stop()
