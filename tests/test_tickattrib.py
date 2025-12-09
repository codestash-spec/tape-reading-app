import pytest


def test_tick_attrib_imports():
    ibapi = pytest.importorskip("ibapi")
    from ibapi.common import TickAttribBidAsk, TickAttribLast

    assert isinstance(TickAttribBidAsk(), TickAttribBidAsk)
    assert isinstance(TickAttribLast(), TickAttribLast)
