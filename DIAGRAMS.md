# Diagrams

## EventBus flow
```mermaid
sequenceDiagram
    participant Provider
    participant Normalizer
    participant Bus
    participant Engine
    Provider->>Normalizer: Raw callback
    Normalizer->>Bus: MarketEvent(event_type)
    Bus-->>Engine: Dispatch by event_type
    Engine-->>Bus: (optional) Derived events
```

## MarketEvent transformation pipeline (IBKR)
```mermaid
flowchart LR
    A[IBKR tick/DOM callback] --> B[ibkr_events builders]
    B --> C[MarketEvent]
    C --> D[EventBus.publish]
    D --> E[DOM/Delta/Tape Engines]
```

## Provider -> Engine -> UI overview
```mermaid
flowchart LR
    Providers --> Bus[EventBus]
    Bus --> Engines[Engines (DOM/Delta/Tape/Footprint)]
    Engines --> UI[UI Panels]
    Engines --> Exec[Execution/Risk]
```

## DOM Engine processing
```mermaid
flowchart LR
    Delta[DOM deltas (MarketEvent.dom_delta)] --> State[DOM Engine state store]
    State --> Ladder[DOM ladder snapshot]
    Ladder --> Outputs[UI panels / replay snapshots]
```

## DOM Engine placeholder (future)
```mermaid
flowchart TB
    subgraph DOMEngine
        A[Receive dom_delta] --> B[Update ladder levels]
        B --> C[Compute spreads/imbalance]
        C --> D[Emit dom_snapshot]
    end
    D --> UI[DOM Ladder UI]
```

## Delta Engine processing
```mermaid
flowchart LR
    Trades[Trade/Tick events] --> Agg[Aggressor inference]
    Agg --> Bars[Delta bars / footprint cells]
    Bars --> Signals[Imbalance & absorption signals]
    Signals --> Consumers[UI / Execution / Risk]
```

## Replay engine pipeline
```mermaid
flowchart LR
    Files[CSV/JSON datasets] --> Loader[HistoricalLoader]
    Loader --> Bus[EventBus.publish]
    Bus --> Engines[Engines/UI subscribers]
```

## Top-level system
```mermaid
flowchart LR
    subgraph Providers
        IB[IBKR]
        DX[dxFeed]
        Hist[Historical Replay]
    end
    subgraph Core
        Norm[Normalization (MarketEvent)]
        EB[EventBus]
    end
    subgraph Engines
        DOM[DOM Engine]
        DELTA[Delta Engine]
        TAPE[Tape/Footprint]
        PAT[Patterns/ML]
    end
    subgraph Execution
        MT5[MT5 Adapter]
        IBX[IBKR Orders]
        RISK[Risk Engine]
    end
    Providers --> Norm --> EB --> Engines --> Execution
    EB --> UI[UI Panels]
```
