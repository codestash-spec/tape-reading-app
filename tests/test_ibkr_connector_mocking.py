from __future__ import annotations

import pytest

pytest.importorskip("ibapi")
import ibkr.ibkr_connector as connector_module  # noqa: E402


def test_ibkr_connector_can_be_instantiated_without_network(monkeypatch, event_bus):
    """
    Demonstrates the recommended mocking strategy for IBKRConnector:
    - Stub EClient.connect to avoid network.
    - Skip thread start and subscription side effects.
    - Skip sleep delays.
    """
    connect_args = {}

    monkeypatch.setattr(
        connector_module.EClient,
        "connect",
        lambda self, host, port, client_id: connect_args.setdefault("called", (host, port, client_id)),
    )
    monkeypatch.setattr(connector_module.threading.Thread, "start", lambda self: None)
    monkeypatch.setattr(connector_module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(connector_module.IBKRConnector, "_subscribe_all", lambda self: None)

    connector = connector_module.IBKRConnector(event_bus, host="h", port=1, client_id=2, symbol="SYM")

    assert connect_args["called"] == ("h", 1, 2)
    assert connector.symbol == "SYM"
