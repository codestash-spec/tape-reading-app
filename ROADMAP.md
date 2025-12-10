# Roadmap

## Phases
- **Fase I - Core Foundation (v0.1.0) - Status: Done**
  - EventBus, MarketEvent, conector IBKR mínimo.
- **Fase II - Providers Layer (v0.2.0) - Status: Done**
  - Normalização IBKR (tick/DOM/L1), Historical Replay (CSV/JSON), mocking IBKR.
- **Fase III - Engines, Strategy, Risk, Execution (v0.3.0) - Status: Done**
  - Engines DOM/Delta/Tape/Footprint, estratégia, risco pré-trade, execução sim/IBKR, telemetria/config.
- **Fase IV - UI Panels - Status: Todo**
  - PySide6: DOM ladder, Tape, Footprint, T&S.
- **Fase V - Execution Router Enhancements - Status: Todo**
  - IBKR/MT5 avançado, retry/backoff, smart routing.
- **Fase VI - Risk Engine Expansion - Status: Todo**
  - Circuit breakers, price collars, métricas/alertas.
- **Fase VII - Replay Engine Expansion - Status: Todo**
  - Stateful replay, clocks sincronizados, checkpointing.
- **Fase VIII - Pattern Detector - Status: Todo**
  - Biblioteca de sinais (DOM/Delta/Tape/Footprint).
- **Fase IX - ML Engine - Status: Todo**
  - Pipelines de features, inferência, gestão de modelos.
- **Fase X - Backtesting/Simulation - Status: Todo**
  - Runner de cenários, métricas PnL/latência.
- **Fase XI - Packaging / Deployment / SaaS - Status: Todo**
  - Empacotamento, CI/CD, observabilidade, multi-tenant.

## Milestones
- UI institucional com feeds/replay.
- Execução avançada com SLAs e auditoria reforçada.
- Risco expandido com circuit breakers e collar operacional.
- Pattern/ML engines para sinais compostos.
- Backtesting e oferta SaaS com observabilidade.
