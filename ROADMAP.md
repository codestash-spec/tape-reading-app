# Roadmap

## Phases
- **Fase I – Core Foundation (v0.1.0) – Status: Done**
  - Scope: EventBus, canonical MarketEvent, minimal IBKR connector.
  - Tasks: Thread-safe dispatch, schema aliases, baseline docs/tests.
- **Fase II – Providers Layer (v0.2.0) – Status: Done**
  - Scope: IBKR normalization (tick-by-tick, DOM delta, L1 fallback), historical replay loader.
  - Tasks: Builders in `ibkr_events`, replay CSV/JSON loader, IBKR mocking guidance.
- **Fase III – Engines (DOM, Delta, Tape, Footprint) – Status: Todo (target v0.3.0)**
  - Scope: In-memory DOM ladder, delta/footprint aggregators, tape view.
  - Tasks: Engine scaffolding, state stores, unit tests, replay compatibility.
- **Fase IV – UI Panels – Status: Todo**
  - Scope: PySide6 panels for DOM ladder, Tape, Footprint, T&S.
  - Tasks: EventBus subscriptions, layouts, refresh throttling, theme tokens.
- **Fase V – Execution Router – Status: Todo**
  - Scope: IBKR + MT5 adapters, order routing from engine signals.
  - Tasks: Order abstraction, retry/backoff, audit logging, dry-run mode.
- **Fase VI – Risk Engine – Status: Todo**
  - Scope: Limits, exposure, throttles, kill-switch.
  - Tasks: Pre-trade checks, circuit breakers, metrics/alerts.
- **Fase VII – Replay Engine Expansion – Status: Todo**
  - Scope: Stateful replay, synchronized clocks, checkpointing.
  - Tasks: Deterministic timing, pause/resume, seek, snapshot export.
- **Fase VIII – Pattern Detector – Status: Todo**
  - Scope: Signal library over DOM/Delta/Tape/Footprint.
  - Tasks: Signal DSL, scoring, alert routing.
- **Fase IX – ML Engine – Status: Todo**
  - Scope: Feature pipelines, inference harness, model management.
  - Tasks: Offline feature store, on-demand inference, drift checks.
- **Fase X – Backtesting/Simulation – Status: Todo**
  - Scope: Scenario runner, multi-provider simulation, metrics.
  - Tasks: Deterministic seeds, PnL/latency reporting, strategy hooks.
- **Fase XI – Packaging / Deployment / SaaS – Status: Todo**
  - Scope: Packaging, CI/CD, observability, tenancy model.
  - Tasks: Versioned releases, containerization, dashboards, SLA hooks.

## Milestones
- Harden normalization layer for IBKR and add dxFeed parity.
- Deliver DOM and Delta engines with snapshot + incremental state and tests.
- Ship UI panels for DOM/Tape/Footprint with replay support.
- Add execution adapters with risk gating and audit logging.
- Introduce pattern recognition and ML pipelines for signal generation.
- Finalize backtesting engine and SaaS packaging with observability.
