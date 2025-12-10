# TELEMETRY.md — Logs, Métricas, Tracing, Auditoria

## Logging JSON
Campos emitidos por `core/logging.py`:
- `ts` (ISO UTC), `level`, `component`, `message`
- `trace_id`, `span_id`
- `symbol`, `order_id`, `signal_id`
- `context`
- `env`, `pid`

Saída em stdout (JSON lines), pronta para coletores (ELK/OTel).

## Métricas
`telemetry/metrics.py`: counters/gauges in-memory.
- `incr(name, value)`, `observe(name, value)`, `snapshot()`.

## Tracing
`telemetry/tracing.py` + `core/telemetry.py`:
- `TraceSpan` com `name`, `attributes`, `status`, `duration_ms`, `error`.
- `traced_span(name, attrs, metrics)` para medir e registrar erros/duração.

## Auditoria
`telemetry/audit.py`: linha JSON com `ts`, `event_type`, `payload`.
- Para integridade: aplicar hash-chaining ou storage append-only no pipeline de logs.
- Eventos críticos: risco (decisões), execução (acks/fills/rejects), kill-switch.

## Dashboards e Observabilidade
- Filtrar logs por `component/symbol/order_id`.
- Expor métricas/traces a Prometheus/OTel via adaptadores futuros.
- Correlação de ingestão→estratégia→risco→execução via `trace_id`.
