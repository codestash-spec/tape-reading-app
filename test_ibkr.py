import argparse
import signal
import sys
import time
from typing import List

from core.event_bus import EventBus
from ibkr.ibkr_connector import IBKRConnector


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Minimal IBKR connectivity smoke test.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7497)
    parser.add_argument("--client-id", type=int, default=1)
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--seconds", type=int, default=10, help="How long to listen before exiting.")
    args = parser.parse_args(argv)

    bus = EventBus()

    def on_event(evt):
        print(f"[{evt.event_type.upper()}] {evt.symbol} {evt.payload}")

    bus.subscribe("tick", on_event)
    bus.subscribe("trade", on_event)
    bus.subscribe("dom_delta", on_event)

    connector = IBKRConnector(
        bus,
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        symbol=args.symbol,
    )

    stop = False

    def handle_sigint(sig, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_sigint)

    print(f"[IBKR TEST] Listening for {args.seconds}s... Press Ctrl+C to stop early.")
    start = time.time()
    while not stop and (time.time() - start) < args.seconds:
        time.sleep(0.25)

    print("[IBKR TEST] Stopping...")
    connector.stop(timeout=2.0)
    bus.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
