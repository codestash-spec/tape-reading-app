# Tape Reading App

Institutional-grade tape reading & orderflow platform (Bookmap/Jigsaw style) built on an event-driven architecture. Designed for quant teams needing a clean pipeline from IBKR market data into DOM/Delta/Tape/Footprint engines, UI panels, and execution adapters.

## Who this is for
- Quant / trading tech teams building real-time orderflow analytics.
- Engineers needing a normalized market data contract and replayable event stream.
- Contributors who want a well-documented, testable Python 3.x + Pydantic v2 stack.

## Key features
- Thread-safe `EventBus` for high-frequency publish/subscribe.
- Canonical `MarketEvent` model with aliases for provider compatibility.
- IBKR provider: tick-by-tick (bid/ask + trades), DOM deltas, Level 1 fallback.
- Historical replay provider for CSV/JSON streams.
- Future engines: DOM, Delta, Tape, Footprint, Pattern Detector.
- Future UI: PySide6 institutional panels (DOM ladder, Delta, Footprint, T&S).
- Future execution: IBKR + MT5 adapters with risk gating.

## Architecture summary
Providers -> Normalizers -> EventBus -> Engines -> UI -> Execution
- **Providers**: IBKR live feed; historical replay (dxFeed placeholder).
- **Normalization**: `ibkr_events` converts IB callbacks to `MarketEvent`.
- **Core**: `EventBus` dispatches per `event_type`.
- **Engines (planned)**: DOM/Delta/Tape/Footprint/Patterns consume the bus.
- **UI (planned)**: PySide6 panels subscribe to the bus.
- **Execution (planned)**: IBKR/MT5 adapters consume engine outputs with risk checks.

## Folder structure
```
core/          # Event bus and infra
ibkr/          # IBKR connector + normalization
models/        # MarketEvent and shared schemas
providers/     # Historical replay + provider placeholders
tests/         # Pytest suite, fixtures, IBKR mocking examples
requirements.txt
README.md, ARCHITECTURE.md, ROADMAP.md, CHANGELOG.md, CONTRIBUTING.md, STYLEGUIDE.md, DIAGRAMS.md
```

## Setup
Create and activate a virtualenv (PowerShell example):
```
python -m venv .venv
.\.venv\Scripts\activate
```
Install dependencies:
```
pip install -r requirements.txt
```
Run tests:
```
python -m pytest
```

## Minimal IBKR connection test (manual)
Preconditions: IB Gateway or TWS running (paper), API enabled, socket `127.0.0.1:7497`, market data permissions granted.
```
python test_ibkr.py --symbol XAUUSD --host 127.0.0.1 --port 7497 --client-id 1 --seconds 10
```
This spins up `EventBus`, subscribes to `tick`, `trade`, and `dom_delta`, connects via `IBKRConnector`, and prints events for the given duration.

## Tick-by-tick vs Level 1 fallback
1) Attempt tick-by-tick (BidAsk + AllLast); publish normalized `MarketEvent.tick`/`trade`.
2) Always request DOM depth (updateMktDepthL2) and publish `dom_delta`.
3) If tick-by-tick fails, automatically switch to Level 1 `reqMktData`, publishing simplified ticks.

## Historical replay mode
Use `providers.HistoricalLoader` to load and replay CSV/JSON as live events:
```python
from providers.historical_loader import HistoricalLoader
from core.event_bus import EventBus

bus = EventBus()
loader = HistoricalLoader(bus)
loader.load_json("data/events.json")  # or loader.load_csv("data/events.csv")
loader.replay(speed=2.0)
```

## Roadmap (Phases I-XI)
- **v0.1.0 - Fase I**: Core foundation (EventBus, MarketEvent, minimal IBKR).
- **v0.2.0 - Fase II**: Providers layer (IBKR normalization, DOM deltas, historical loader).
- **v0.3.0 (planned) - Fase III**: Engines (DOM, Delta, Tape, Footprint scaffolding).
- **Fase IV**: UI panels (DOM ladder, Tape, Footprint, T&S).
- **Fase V**: Execution router (IBKR + MT5) with risk hooks.
- **Fase VI**: Risk engine (limits, throttles, exposure).
- **Fase VII**: Replay engine expansion (stateful, synchronized clocks).
- **Fase VIII**: Pattern detector (tape/DOM/footprint signals).
- **Fase IX**: ML engine (feature pipelines, inference).
- **Fase X**: Backtesting/simulation harness.
- **Fase XI**: Packaging / deployment / SaaS with observability.

## Next steps for contributors
- Implement DOM and Delta engines with unit tests and replay coverage.
- Add dxFeed adapter matching the MarketEvent contract.
- Build PySide6 UI panels fed by the EventBus.
- Add execution/risk adapters with structured logging and metrics.
