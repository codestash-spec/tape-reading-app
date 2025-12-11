from core.instrument_detector import detect_instrument


def test_autodetect_fx():
    info = detect_instrument("XAUUSD")
    assert info["instrument_type"] == "FX"
    assert info["market_provider"] == "IBKR"


def test_autodetect_cfd():
    info = detect_instrument("XAUUSD.CFD")
    assert info["instrument_type"] == "CFD"
    assert info["market_provider"] == "IBKR"


def test_autodetect_futures():
    info = detect_instrument("GCZ4")
    assert info["instrument_type"] == "FUTURES"
    assert info["market_provider"] == "IBKR"


def test_autodetect_binance():
    info = detect_instrument("XAUUSDT")
    assert info["market_provider"] == "BINANCE"


def test_autodetect_okx():
    info = detect_instrument("XAUTUSDT")
    assert info["market_provider"] == "OKX"


def test_autodetect_sim():
    info = detect_instrument("UNKNOWN")
    assert info["instrument_type"] == "SIM"
