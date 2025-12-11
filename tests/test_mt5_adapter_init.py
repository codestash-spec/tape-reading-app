import types

from execution.mt5_adapter import MT5ExecutionAdapter


def test_mt5_adapter_init(monkeypatch):
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
    adapter = MT5ExecutionAdapter(bus=None, symbol_map={"BTCUSDT": "BTCUSD"}, default_volume=0.01, dry_run=True)
    assert adapter.mt5 is fake_mt5
