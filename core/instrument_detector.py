from __future__ import annotations

from typing import Dict


def detect_instrument(symbol: str) -> Dict[str, str]:
    """
    Basic heuristic instrument detector.
    """
    sym = symbol.upper()
    res = {
        "instrument_type": "SIM",
        "market_provider": "SIM",
        "execution_provider": "SIM",
        "normalized_symbol": sym,
    }
    fx_list = {"XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"}
    cfd_tokens = ("CFD", "_IBKR", ".FPM")
    binance_tokens = ("XAUUSDT", "GOLDUSDT", "BTCUSDT", "ETHUSDT")
    okx_tokens = ("XAUTUSDT", "GOLDUSDT.OKX", "XAUT/USDT")
    fut_tokens = ("GC", "GOLD")

    if sym in fx_list:
        res.update(
            {
                "instrument_type": "FX",
                "market_provider": "IBKR",
                "execution_provider": "IBKR",
                "normalized_symbol": sym,
            }
        )
    elif any(t in sym for t in cfd_tokens):
        res.update(
            {
                "instrument_type": "CFD",
                "market_provider": "IBKR",
                "execution_provider": "IBKR",
                "normalized_symbol": sym.replace(".CFD", "").replace("_IBKR", "").replace(".FPM", ""),
            }
        )
    elif any(sym.startswith(t) for t in binance_tokens):
        res.update(
            {
                "instrument_type": "CRYPTO_BINANCE",
                "market_provider": "BINANCE",
                "execution_provider": "SIM",
                "normalized_symbol": sym,
            }
        )
    elif any(sym.startswith(t) for t in okx_tokens):
        res.update(
            {
                "instrument_type": "CRYPTO_OKX",
                "market_provider": "OKX",
                "execution_provider": "SIM",
                "normalized_symbol": sym,
            }
        )
    elif any(sym.startswith(t) for t in fut_tokens):
        res.update(
            {
                "instrument_type": "FUTURES",
                "market_provider": "IBKR",
                "execution_provider": "IBKR",
                "normalized_symbol": sym,
            }
        )
    return res
