# Phase V — Camada de Estratégia Institucional

## Objetivo
Construir uma camada de orquestração de estratégia institucional com playbooks, confluência, regimes e pontuação de sinais usando microestrutura e filtros macro.

## Componentes
- StrategyOrchestrator: loop principal ligado ao EventBus.
- PlaybookEngine: regras de entrada/validação por confluência.
- ConfluenceFramework: filtros de spoof/liquidez/volatilidade.
- RegimeEngine: ATR, volume e sessões como gates.
- SignalScorer: pontuação baseada em features/tagging.
- Pipelines de features: `MicrostructureFeatureExtractor` + ML-ready.

## Fluxo de Sinais
```mermaid
flowchart LR
    MS[Microstructure Snapshot] --> Playbook
    Playbook --> Confluence
    Confluence --> Regime
    Regime --> Score[Scoring]
    Score --> Signal
    Signal --> BUS(EventBus signal)
    BUS --> Risk[Risk Engine]
```

## Estados e Cooldowns
- Controle por símbolo, cooldown configurável.
- Tags enriquecem metadados e pesam na pontuação.

## Interfaces
- Entrada: evento `microstructure` (payload.snapshot.features/tags)
- Saída: evento `signal` com `direction`, `score`, `confidence` e `features` completos

## Resiliência
- Regimes evitam operação em ambientes extremos.
- Confluência bloqueia sinais em spoof/liquidez suspeita.
- Filtros determinísticos para testes reprodutíveis.
