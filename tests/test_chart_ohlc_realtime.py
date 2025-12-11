import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.ohlc.engine import OHLCEngine
from models.market_event import MarketEvent


def test_chart_ohlc_realtime():
    bus = EventBus()
    ohlc = OHLCEngine(bus, timeframe_seconds=1)
    bars = []
    bus.subscribe("chart_ohlc", lambda evt: bars.append(evt.payload))
    evt = MarketEvent(event_type="trade", timestamp=datetime.now(timezone.utc), source="sim", symbol="BTCUSDT", payload={"price": 100.0, "size": 1.0})
    bus.publish(evt)
    time.sleep(0.1)
    bus.stop()
    assert bars, "Expected at least one OHLC update"
