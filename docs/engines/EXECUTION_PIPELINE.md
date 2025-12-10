# EXECUTION_PIPELINE.md — Fluxo de Execução Institucional

## Modelos de Ordem
`OrderRequest`: `order_id`, `symbol`, `side`, `quantity`, `order_type` (market/limit/stop/stop_limit), `limit_price`, `stop_price`, `tif`, flags (`post_only`, `reduce_only`, `dry_run`), `routing_hints`, `metadata`.

`OrderEvent`: `order_id`, `symbol`, `status` (`ack`, `partial_fill`, `fill`, `reject`, `cancel`, `error`), `timestamp`, `filled_qty`, `avg_price`, `reason`, `raw`.

## Pré-trade Risco
- RiskEngine: kill-switch, whitelist, tamanho, exposição, throttle.
- Price collar conceitual disponível via helper.
- Decisão `RiskDecision` publicada como `risk_decision` (opcional) para telemetria.

## Roteamento
- `ExecutionRouter.submit(order)`: envia ao adaptador, mantém mapa, publica `order_event`.
- `cancel`, `replace`: propagam ao adaptador.

## Adaptadores
- **SimAdapter**: ACK imediato, fill com probabilidade configurável (default 100%), eventos `order_event`.
- **IBKRAdapter (stub)**: mapeia para `Contract` FX e `Order` IBKR, envia via IB API, publica ACK local; callbacks publicam parciais/fills/rejects/cancels.

## Integração EventBus
- `order_event` no `EventBus`; consumidores: estratégia, risco pós-trade, telemetria.

## Erros e Recuperação
- Sim: determinístico, sem falhas de transporte.
- IBKR: em falha, acionar cancel/kill-switch; evoluções futuras para retry/backoff/rotas alternativas.
