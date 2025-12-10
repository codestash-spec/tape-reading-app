# DIAGRAMS.md — Diagramas Integrados

## Arquitetura Geral
```mermaid
flowchart LR
    subgraph Ingest
        IB[IBKR Realtime]
        Replay[Historical Replay]
        DX[Future dxFeed]
    end
    subgraph Normalize
        IE[ibkr_events]
        ME[MarketEvent Schema]
    end
    subgraph Core
        EB[EventBus]
    end
    subgraph Engines
        DOM[DOM Engine]
        DELTA[Delta Engine]
        TAPE[Tape Engine]
        FOOT[Footprint Engine]
        STRAT[Strategy Engine]
    end
    subgraph RiskExec
        RISK[Risk Engine]
        EXEC[Execution Router]
        ADAPT[Adapters: ibkr/sim]
    end
    subgraph Telemetry
        LOGS[JSON Logs]
        METRICS[Metrics/Tracing]
        AUDIT[Audit Trail]
    end
    Ingest --> Normalize --> EB --> Engines --> RiskExec
    Engines --> Telemetry
    RiskExec --> Telemetry
    EB --> Telemetry
    RISK --> EXEC
    EXEC --> ADAPT
```

## Data Pipeline
```mermaid
flowchart LR
    IB[IBKR API] --> Raw[Raw callbacks]
    Replay[CSV/JSON Replay] --> Raw
    Raw --> Norm[Normalization (ibkr_events)]
    Norm --> ME[MarketEvent]
    ME --> Bus[EventBus.publish]
    Bus --> Engines[Engines State]
    Engines --> Strat[Strategy]
    Strat --> Risk[Risk Engine]
    Risk --> Exec[Execution Router]
    Exec --> Adapters[Adapters ibkr/sim]
```

## Signal Flow
```mermaid
flowchart LR
    Tick[Tick/Trade/DOM Events] --> Feat[Feature/State Updates]
    Feat --> Strat[Strategy Logic]
    Strat --> Signal[Signal Event]
    Signal --> Risk[Risk Decision]
    Risk -->|Approve| Order[OrderRequest]
    Risk -->|Reject| LogR[Risk Reject Log]
    Order --> Exec[Execution Router]
    Exec --> Adapter[Adapter]
    Adapter --> Fills[Order Events]
    Fills --> Strat
    Fills --> Telemetry
```

## Execution Flow
```mermaid
flowchart LR
    Signal[Signal Event] --> Risk
    Risk -->|Approve| Router[Execution Router]
    Risk -->|Reject| Reject[Reject/Log]
    Router --> Adapter[Adapter ibkr/sim]
    Adapter --> Bus[order_event -> EventBus]
    Bus --> Consumers[Strategy/Risk/Telemetry]
```

## Risk Decision Tree
```mermaid
flowchart TD
    Start[Order Intent] --> Kill[Kill-switch engaged?]
    Kill -->|Yes| RejectKS[Reject: kill-switch]
    Kill -->|No| Sym[Symbol whitelisted?]
    Sym -->|No| RejectSym[Reject: symbol]
    Sym -->|Yes| Size[Within size limit?]
    Size -->|No| RejectSize[Reject: size_limit]
    Size -->|Yes| Expo[Within exposure cap?]
    Expo -->|No| RejectExpo[Reject: exposure_limit]
    Expo -->|Yes| Throt[Throttle window ok?]
    Throt -->|No| RejectThrot[Reject: throttle_exceeded]
    Throt -->|Yes| Approve[Approve -> Execution]
```

## Failure & Recovery
```mermaid
flowchart LR
    Fault[Fault Detected] --> Classify[Classify: Feed | Exec | Risk | Infra]
    Classify --> FeedStale[Feed Stale] --> Action1[Fallback L1 / Alert / Halt strategies]
    Classify --> ExecErr[Execution Error] --> Action2[Retry/Cancel/Route sim]
    Classify --> RiskTrip[Risk Trip] --> Action3[Engage Kill-switch + Cancel]
    Classify --> Infra[Infra/Process] --> Action4[Restart worker / Replay]
    Action1 --> Telemetry[Log/Audit/Metrics]
    Action2 --> Telemetry
    Action3 --> Telemetry
    Action4 --> Telemetry
```
