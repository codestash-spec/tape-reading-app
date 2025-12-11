from datetime import datetime, timezone

from core.event_bus import EventBus
from models.market_event import MarketEvent
from providers.provider_base import ProviderBase
from providers.provider_manager import ProviderManager


class DummyProvider(ProviderBase):
    def __init__(self, bus, settings, symbol):
        super().__init__(bus, settings, symbol)
        self.started = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False

    def subscribe_dom(self) -> None:
        return None

    def subscribe_trades(self) -> None:
        return None

    def subscribe_quotes(self) -> None:
        return None

    def normalize_dom(self, raw):
        return MarketEvent(event_type="dom_snapshot", timestamp=datetime.now(timezone.utc), source="sim", symbol=self.symbol, payload={})

    def normalize_trade(self, raw):
        return MarketEvent(event_type="trade", timestamp=datetime.now(timezone.utc), source="sim", symbol=self.symbol, payload={})


def test_provider_switch_engine_reset():
    bus = EventBus()
    settings = {"symbols": ["BTCUSDT"], "market_symbol": "BTCUSDT", "ui": {}}
    pm = ProviderManager(bus, settings)
    pm.providers = {
        "BINANCE": DummyProvider(bus, settings, "BTCUSDT"),
        "SIM": DummyProvider(bus, settings, "BTCUSDT"),
    }
    pm.start("BINANCE")
    assert pm.active_name == "BINANCE"
    assert pm.providers["BINANCE"].started
    pm.start("SIM")
    assert pm.active_name == "SIM"
    assert not pm.providers["BINANCE"].started
    bus.stop()


def test_engine_cleanup_no_ghost_events():
    bus = EventBus()
    called = []
    bus.allowed_sources = {"sim"}
    bus.subscribe("dom_snapshot", lambda evt: called.append(evt))
    evt_ok = MarketEvent(event_type="dom_snapshot", timestamp=datetime.now(timezone.utc), source="sim", symbol="X", payload={})
    evt_ghost = MarketEvent(event_type="dom_snapshot", timestamp=datetime.now(timezone.utc), source="ghost", symbol="X", payload={})
    bus.publish(evt_ok)
    bus.publish(evt_ghost)
    bus.stop()
    assert len(called) == 1
