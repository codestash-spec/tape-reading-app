import threading
import time

import pytest

from core.event_bus import EventBus
from models.market_event import MarketEvent
from datetime import datetime, timezone


def make_evt(et="tick", sym="ES"):
    return MarketEvent(event_type=et, timestamp=datetime.now(timezone.utc), source="test", symbol=sym, payload={"p": 1})


def test_subscribe_unsubscribe():
    bus = EventBus()
    hits = []

    def cb(evt):
        hits.append(evt)

    bus.subscribe("tick", cb)
    bus.publish(make_evt("tick"))
    time.sleep(0.05)
    bus.unsubscribe("tick", cb)
    bus.publish(make_evt("tick"))
    time.sleep(0.05)
    bus.stop()
    assert len(hits) == 1


def test_high_frequency_dispatch():
    bus = EventBus()
    count = 0
    lock = threading.Lock()

    def cb(evt):
        nonlocal count
        with lock:
            count += 1

    bus.subscribe("tick", cb)
    for _ in range(2000):
        bus.publish(make_evt("tick"))
    time.sleep(0.2)
    bus.stop()
    assert count == 2000


def test_multithread_publish():
    bus = EventBus()
    count = 0
    lock = threading.Lock()

    def cb(evt):
        nonlocal count
        with lock:
            count += 1

    bus.subscribe("tick", cb)

    def worker(n):
        for _ in range(n):
            bus.publish(make_evt("tick"))

    threads = [threading.Thread(target=worker, args=(200,)) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    time.sleep(0.2)
    bus.stop()
    assert count == 1000


def test_stop_drains_queue():
    bus = EventBus()
    hits = []

    def cb(evt):
        hits.append(evt)

    bus.subscribe("tick", cb)
    bus.publish(make_evt("tick"))
    bus.stop()
    assert len(hits) >= 1
