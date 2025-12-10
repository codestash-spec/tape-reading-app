# DEVELOPER_GUIDE.md — Guia do Desenvolvedor

## Ambiente
- Python 3.11+ recomendado.
- Criar venv: `python -m venv .venv && .\.venv\Scripts\activate` (PowerShell).
- Instalar deps: `pip install -r requirements.txt`.
- Executar testes: `python -m pytest`.

## Estrutura do Código
```
core/        # EventBus, config loader, logging/telemetry helpers
models/      # MarketEvent, Signal, Order, RiskDecision, State
ibkr/        # Connector, normalizers, order builders, health
providers/   # HistoricalLoader, replay_clock, dxfeed placeholder
engines/     # dom, delta, tape, footprint, strategy, ml_features
risk/        # engine, rules, kill_switch, limits.yaml
execution/   # router, adapters (ibkr, sim), order_book_router
telemetry/   # logger, metrics, tracing, audit
config/      # settings, profiles, secrets.example
tests/       # pytest suite
```

## Princípios de Código
- Tipagem obrigatória; Pydantic para modelos; imutabilidade onde possível.
- Logging estruturado; sem `print`.
- Funções pequenas, responsabilidade única; modularidade por domínio.
- Forward compatibility: `MarketEvent` ignora extras; aliases para campos críticos.

## Fluxo de Desenvolvimento
1. Crie branch `feature/<desc>` ou `fix/<desc>`.
2. Desenvolva com testes (sim/replay); evite dependências externas para unit tests.
3. Rode `python -m pytest`.
4. Atualize docs se alterar contratos/fluxos.
5. Commit com Conventional Commit; abra PR com resumo, riscos, evidências de teste.

## Testes
- `tests/` cobre bus, MarketEvent, pipeline strategy→risk→exec, replay loader, mocking IBKR.
- Adicione fixtures para novos módulos; mantenha determinismo (seed, dados fixos).

## Debug/Tracing
- Use `logging` com `extra` (symbol, order_id).
- `traced_span` para medir blocos críticos.
- Métricas in-memory (`MetricsSink`) para counters/gauges.

## Estilo
- Siga `STYLEGUIDE.md` (nomes, layout, logging).
- Revisão dupla para mudanças em risco/exec.

## Execução Local
- Sim: `python main.py --profile dev --mode sim`
- Live: `python main.py --profile prod --mode ibkr --symbol XAUUSD --host 127.0.0.1 --port 7497`
- Replay: `python run_replay.py --file data/events.json --speed 2.0`
