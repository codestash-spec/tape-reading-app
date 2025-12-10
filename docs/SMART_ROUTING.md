# Smart Routing

## Objetivo
Roteamento institucional com slicing, ETA de fila, peg orders e métricas de execução.

## Componentes
- SmartOrderRouter (SOR)
- Slicing Engine (`slice_order`)
- Queue-time Estimator
- Metrics (slippage/latência)
- Cancel/Replace supervisonado

## Fluxo
```mermaid
flowchart LR
    Risk --> SOR
    SOR --> Slice[Child Orders]
    Slice --> ExecRouter
    ExecRouter --> Adapter[IBKR/Sim]
    Adapter --> Events[order_event]
    Events --> SOR
    Events --> Telemetry
```

## Funcionalidades
- Clip-size configurável
- Metadata ETA por child order
- Peg mid/iceberg sintética
- Health superficial via `router_action`

## Métricas
- slippage_bps_avg, latency_ms_avg, fills
