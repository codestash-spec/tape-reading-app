import time
from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.ohlc.engine import OHLCEngine
from engines.volume_profile.engine import VolumeProfileEngine
from engines.liquidity_map.engine import LiquidityMapEngine
from engines.microstructure.engine import MicrostructureEngine
from models.market_event import MarketEvent


def test_btcusdt_data_flow_simulated():
    bus = EventBus()
    dom_seen = []
    tape_seen = []
    fp_seen = []
    ohlc_seen = []

    # engines
    ohlc = OHLCEngine(bus, timeframe_seconds=1)
    vp = VolumeProfileEngine(bus)
    liq = LiquidityMapEngine(bus)
    micro = MicrostructureEngine(bus, ["BTCUSDT"])
    micro.start()

    bus.subscribe("dom_snapshot", lambda evt: dom_seen.append(evt))
    bus.subscribe("trade", lambda evt: tape_seen.append(evt))
    bus.subscribe("microstructure", lambda evt: fp_seen.append(evt))
    bus.subscribe("chart_ohlc", lambda evt: ohlc_seen.append(evt))

    # push DOM
    dom_evt = MarketEvent(
        event_type="dom_snapshot",
        timestamp=datetime.now(timezone.utc),
        source="binance",
        symbol="BTCUSDT",
        payload={"dom": [{"price": 100.0, "bid_size": 10.0, "ask_size": 0.0}, {"price": 100.1, "bid_size": 0.0, "ask_size": 8.0}]},
    )
    bus.publish(dom_evt)

    # push trade
    trade_evt = MarketEvent(
        event_type="trade",
        timestamp=datetime.now(timezone.utc),
        source="binance",
        symbol="BTCUSDT",
        payload={"price": 100.05, "size": 2.0, "side": "buy"},
    )
    bus.publish(trade_evt)

    time.sleep(0.05)
    bus.stop()

    assert dom_seen, "DOM should be received"
    assert tape_seen, "Trades should be received"
    assert fp_seen, "Microstructure/footprint should be emitted"
    assert ohlc_seen, "OHLC should be emitted"
