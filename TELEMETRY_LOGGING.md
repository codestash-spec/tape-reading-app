# TELEMETRY_LOGGING.md — Telemetria, Logging, Tracing e Auditoria

## Logging Estruturado
- Formato JSON emitido por `core/logging.py`.
- Campos: `ts`, `level`, `component`, `message`, `trace_id`, `span_id`, `symbol`, `order_id`, `signal_id`, `context`, `env`, `pid`.
- Saída em stdout (JSON lines) → coletores (ELK/OTel).
- Preferir `logging` a `print`; incluir IDs de negócio em `extra`.

## Métricas
- `telemetry/metrics.py`: counters/gauges in-memory.
- API: `incr(name, value)`, `observe(name, value)`, `snapshot()`.
- Uso: latência de spans, profundidade de fila, taxas de rejeição de risco, fills, quedas de feed.

## Tracing
- `telemetry/tracing.py` + `core/telemetry.py`.
- `TraceSpan`: `name`, `attributes`, `status`, `duration_ms`, `error`.
- `traced_span(name, attrs, metrics)` para medir blocos críticos (normalização, estratégia, risco, execução).
- Correlacionar eventos com `trace_id`/`span_id` em logs e `MarketEvent`.

## Auditoria
- `telemetry/audit.py`: linha JSON com `ts`, `event_type`, `payload`.
- Recomenda-se hash-chaining ou armazenamento append-only para integridade.
- Eventos-chave: `risk_decision`, `order_event` (ack/fill/reject/cancel), `kill_switch`.

## Dashboards e Observabilidade
- Logs: filtros por `component`, `symbol`, `order_id`, `signal_id`.
- Métricas: exportáveis a Prometheus/OTel via adaptadores futuros.
- Tracing: reconstrução ponta-a-ponta (ingestão→estratégia→risco→execução).

## Boas Práticas
- Granularidade: INFO para fluxo normal; WARN/ERROR para falhas; DEBUG apenas em dev/replay.
- Evitar logs em loops apertados de alta frequência; usar amostragem ou throttling.
- Incluir contexto mínimo de negócio (symbol, order_id, reqId, client_id).
