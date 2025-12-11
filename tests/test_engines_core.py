from datetime import datetime, timezone

from core.event_bus import EventBus
from engines.dom import DOMEngine
from engines.delta import DeltaEngine
from engines.footprint import FootprintEngine
from engines.tape import TapeEngine
from models.market_event import MarketEvent


def make_evt(et, symbol="ES", payload=None):
    return MarketEvent(event_type=et, timestamp=datetime.now(timezone.utc), source="test", symbol=symbol, payload=payload or {})


def test_dom_engine_snapshot():
    bus = EventBus()
    dom = DOMEngine(bus)
    evt = make_evt("dom_delta", payload={"side": "bid", "level": 0, "operation": "insert", "price": 100, "size": 50})
    bus.publish(evt)
    snap = dom.snapshot("ES")
    assert snap.event_type == "dom_snapshot"
    assert snap.payload["bids"]["0"]["price"] == 100
    bus.stop()


def test_delta_engine_accumulates():
    bus = EventBus()
    delta = DeltaEngine(bus)
    bus.publish(make_evt("trade", payload={"price": 100, "size": 10, "aggressor": "buy"}))
    bus.publish(make_evt("trade", payload={"price": 99, "size": 5, "aggressor": "sell"}))
    st = delta.state["ES"].delta_bar
    assert st.buys == 10
    assert st.sells == 5
    bus.stop()


def test_footprint_engine():
    bus = EventBus()
    fp = FootprintEngine(bus)
    bus.publish(make_evt("trade", payload={"price": 100, "size": 5, "aggressor": "buy"}))
    bus.publish(make_evt("trade", payload={"price": 100, "size": 3, "aggressor": "sell"}))
    snap = fp.snapshot("ES")
    level = [x for x in snap.payload if x["price"] == 100][0]
    assert level["buy"] == 5
    assert level["sell"] == 3
    bus.stop()


def test_tape_engine():
    bus = EventBus()
    tape = TapeEngine(bus, max_events=2)
    bus.publish(make_evt("trade", payload={"price": 1, "size": 1}))
    bus.publish(make_evt("trade", payload={"price": 2, "size": 2}))
    snap = tape.snapshot("ES")
    assert len(snap.payload) == 2
    bus.stop()
