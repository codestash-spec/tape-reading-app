# PROJECT_OVERVIEW.md — Bots Institucionais – Edição II

## Visão Geral
Plataforma institucional para leitura de tape e automação de execução sobre dados IBKR, construída em Python 3.x com arquitetura orientada a eventos. O núcleo provê normalização de mercado, transporte via EventBus, engines de estado (DOM/Delta/Tape/Footprint), estratégia, risco pré-trade, execução (sim/IBKR) e telemetria estruturada. Modos suportados: sim, live e replay.

## Fases
- **Fase I**: Fundamentos — `MarketEvent`, `EventBus`, conector IBKR mínimo.
- **Fase II**: Provedores — normalização IBKR (tick/DOM/L1), Historical Replay.
- **Fase III**: Engines/Strategy/Risk/Execution — DOM/Delta/Tape/Footprint, estratégia, risco, roteamento de ordens, telemetria, configuração.
- **Fase IV (planejada)**: UI institucional (PySide6), observabilidade UI.

## Componentes Principais
- **Market Data**: IBKR live + Replay; normalização para `MarketEvent`.
- **Transporte**: `EventBus` thread-safe, subscrição por tipo, wildcard.
- **Engines**: DOM ladder, delta/footprint, tape, agregadores.
- **Estratégia**: event-driven, exemplo micro-price momentum.
- **Risco**: whitelists, limites de tamanho/exposição, throttle, kill-switch.
- **Execução**: Router + adaptadores sim/IBKR; eventos de ordem no bus.
- **Telemetria**: JSON logs, métricas/tracing helpers, audit.
- **Configuração**: YAML + perfis (dev/paper/prod) + env overrides.
- **Governança/Sec**: segredos, papéis, incidentes, kill-switch.

## Modos de Operação
- **Sim**: pipeline completo sem dependência externa.
- **Live (IBKR)**: TWS/IB Gateway; tick/DOM/live orders.
- **Replay**: datasets CSV/JSON com pacing configurável.

## Estrutura do Repositório
```
core/ | models/ | ibkr/ | providers/ | engines/ | risk/ | execution/
telemetry/ | config/ | tests/ | docs (MD) | main.py | run_replay.py
```

## Entrypoints
- `main.py` — live/sim pipeline.
- `run_replay.py` — replay determinístico.

## Operação e Observabilidade
- Logs JSON, métricas/trace helpers, audit.
- Config perfis e overrides por env.
- Runbook para sim/live/replay e kill-switch.
