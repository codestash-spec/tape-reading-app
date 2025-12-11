from execution.router import ExecutionRouter
from execution.adapters.sim import SimAdapter
from execution.mt5_adapter import MT5ExecutionAdapter
from core.event_bus import EventBus


def test_execution_router_mode_switch_sim():
    bus = EventBus()
    sim = SimAdapter(bus)
    router = ExecutionRouter(bus, sim, mode="SIM")
    assert router.mode == "SIM"
    bus.stop()


def test_execution_router_mode_switch_mt5(monkeypatch):
    # fake mt5 module
    import types

    fake_mt5 = types.SimpleNamespace(
        initialize=lambda: True,
        shutdown=lambda: True,
        last_error=lambda: (0, "ok"),
        account_info=lambda: types.SimpleNamespace(login=1234),
        ORDER_TYPE_BUY=0,
        ORDER_TYPE_SELL=1,
        TRADE_ACTION_DEAL=1,
        ORDER_FILLING_IOC=1,
        TRADE_RETCODE_DONE=10009,
        order_send=lambda req: types.SimpleNamespace(retcode=10009, price=req.get("price", 0.0), deal=1, order=1, comment="ok"),
    )
    monkeypatch.setitem(__import__("sys").modules, "MetaTrader5", fake_mt5)
    bus = EventBus()
    mt5 = MT5ExecutionAdapter(bus, {"BTCUSDT": "BTCUSD"}, dry_run=True)
    router = ExecutionRouter(bus, mt5, mode="MT5")
    assert router.mode == "MT5"
    bus.stop()
