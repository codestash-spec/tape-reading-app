# BOTS INSTITUCIONAIS - EDICAO II (Fase III)

Event-driven institutional bot stack (Python 3.x + IBKR) with normalized market data, strategy/risk/execution pipeline, telemetry, and replay harness.

## Core components
- `EventBus`: Thread-safe pub/sub with typed event dispatch.
- `MarketEvent`: Immutable Pydantic schema for all event types.
- Engines: DOM, Delta, Tape, Footprint, Strategy (micro-price momentum example).
- Risk: Whitelist, size, exposure, throttle, kill-switch.
- Execution: Router + IBKR adapter stub + simulator adapter.
- Providers: IBKR market data connector; Historical replay with pacing.
- Telemetry: JSON logging, metrics sink, trace spans, audit emitter.

## Folder structure
```
core/          # Bus, config, telemetry, logging, clocks
models/        # Schemas for events, signals, orders, risk, state
ibkr/          # Connector, events normalization, order mapping, health
providers/     # Historical replay + replay clock
engines/       # DOM, Delta, Tape, Footprint, Strategy, ML features
risk/          # Risk engine, rules, limits, kill-switch
execution/     # Router, adapters (ibkr, sim), order book router
telemetry/     # Logger, metrics, tracing, audit
config/        # Settings and profiles
tests/         # Pytest suite for Phase III pipeline
main.py        # Live pipeline entrypoint
run_replay.py  # Replay pipeline entrypoint
```

## Setup
Create and activate a virtualenv (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Running tests
```
python -m pytest
```

## Live pipeline (IBKR or sim)
```
python main.py --profile dev           # sim mode
python main.py --profile prod --symbol XAUUSD --mode ibkr
```

## Replay pipeline
```
python run_replay.py --file data/events.json --speed 2.0
```

## Minimal IBKR smoke (requires IB Gateway/TWS)
```
python main.py --profile prod --mode ibkr --symbol XAUUSD --host 127.0.0.1 --port 7497
```
