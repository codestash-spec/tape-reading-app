# ADVANCED_ROADMAP.md — Tópicos Avançados e Roteiro de Profissionalização

## Visão Geral
Este roteiro estende as Fases I–IV já implementadas para cobrir os tópicos avançados descritos no manual (Partes V–XIV), organizando-os em fases futuras e pacotes de trabalho.

## Fases Avançadas (propostas)
- **Fase V — Orderflow Engine Avançado**
  - DOM Engine completo (profundidade, rewinds, níveis dinâmicos).
  - Delta Engine avançado (CVD, Speed of Tape, janelas configuráveis).
  - Footprint Engine avançado (imbalances, point of control, volume profile).
  - Signal Engine (absorção, spoofing, imbalances, bursts, failed breakout).
- **Fase VI — Execução Profissional**
  - Execution Engine multi-broker (IBKR, MT5, dual execution).
  - Order Manager & Execution Controller (ciclo completo, partials, replaces).
  - Latency monitor & throughput management; SLAs de execução.
  - UI institucional (DOM/Tape/Footprint/CVD/Heatmap).
- **Fase VII — Abstrações de Feed e Execução**
  - Data Provider Abstraction Layer (multi-feed: IBKR, dxFeed, Rithmic).
  - Execution Abstraction Layer (IBKR, MT5, multi-executor).
  - Price normalization & cross-market mapping (ex.: GC → XAUUSD).
  - Multi-broker architecture e dual execution pipeline.
- **Fase VIII — Feeds Profissionais**
  - Rithmic Integration (bridge C#/Python para orderflow).
  - dxFeed Integration (WebSocket institucional, histórico e replay avançado).
- **Fase IX — Motores Avançados de Dados**
  - Historical Reconstruction (DOM/Footprint/Delta/T&S a partir de brutos).
  - Replay Engine institucional (playback síncrono DOM/Footprint/Delta).
- **Fase X — Risco e Governança Avançados**
  - Risk Engine institucional (Daily DD, exposure hard limits, circuit breakers).
  - Position monitor & trade lifecycle multi-broker.
  - Kill-switch avançado, circuit breakers, monitor de latência e queda de feed.
- **Fase XI — Modelos de Microestrutura e ML**
  - Modelos baseados em microestrutura (seqüenciais, transformers).
  - Pattern detection (absorção, spoofing, bursts, failed breakout).
  - Feature engineering institucional e dataset builder.
  - Training pipeline institucional e thresholds operacionais.
- **Fase XII — Deploy, Infra e Redundância**
  - Deploy institucional (CI/CD, rollback, canary).
  - Redundância de feeds/execução; HA e observabilidade.
- **Fase XIII — Segurança e Governança**
  - Segurança e compliance; segregação de papéis; auditoria reforçada.
  - Gestão de segredos; controles de acesso; evidências de decisão.
- **Fase XIV — Profissionalização**
  - Caminho para operação profissional; checklist de readiness; playbooks.

## Entregáveis-Chave por Bloco
- **Orderflow/Signals**: métricas CVD/SoT; imbalances; detecção de padrões; dashboards.
- **Execução**: multi-broker, rota dual, monitor de latência, tolerância a falhas.
- **Feeds**: abstração, normalização cross-market, fallback e qualidade de feed.
- **Risco**: circuit breakers, limites diários, monitor de posição multi-broker.
- **ML**: features, datasets, pipelines de treino, thresholds operacionais.
- **Ops**: deploy, observabilidade, segurança, governança, profissionalização.
