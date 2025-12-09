import time
from core.event_bus import EventBus
from ibkr.ibkr_connector import IBKRConnector

def on_tick(event):
    print(f"[{event.event_type.upper()}] {event.payload}")

if __name__ == "__main__":
    bus = EventBus()
    bus.subscribe("tick", on_tick)
    bus.subscribe("trade", on_tick)

    ib = IBKRConnector(bus, host="127.0.0.1", port=7497, client_id=1)

    print("Waiting for XAUUSD ticks...")
    while True:
        time.sleep(1)
