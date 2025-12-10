# FEEDS_AND_BROKERS.md — Abstração de Feeds e Execução Multi-Broker

## Objetivo
Desenhar camadas de abstração para múltiplos feeds de mercado e múltiplos brokers de execução, permitindo roteamento flexível, normalização consistente e estratégias de dual execution.

## Data Provider Abstraction Layer
- **Feeds-alvo**: IBKR (live), dxFeed (WebSocket institucional + histórico), Rithmic (bridge C#/Python), futuros feeds.
- **Contratos**: `MarketEvent` como lingua franca; normalização de símbolos, timestamps UTC, agressor, payload estruturado.
- **Qualidade e Fallback**: detecção de staleness, troca de feed, monitor de integridade.
- **Cross-market Mapping**: mapeio de símbolos (ex.: GC → XAUUSD) para alinhar preços/DOM entre mercados e brokers.

## Execution Abstraction Layer
- **Brokers-alvo**: IBKR, MT5, futuras integrações.
- **Adaptadores**: interface comum (`submit/cancel/replace`, eventos `order_event`).
- **Dual Execution**: envio alternado ou redundante para dois brokers; lógica de reconciliação/hedge (futuro).
- **Roteamento e Regras**: hints por símbolo/mercado; tolerância a latência; retry/backoff; cancel/replace seguro.

## Multi-Broker Architecture
- **Mapeamento de símbolos**: futuros vs CFD; ajustes de lote/tick size.
- **Sincronização**: estado de ordens/posições por broker; agregação para risco global.
- **Monitoramento**: latência por rota, rejeições, divergência de preço entre mercados.

## Integração de Feeds Profissionais
- **Rithmic**: feed de orderflow; bridge C# → Python para DOM/tick/trade de alta fidelidade.
- **dxFeed**: WebSocket institucional, histórico e replay; suporte a reconstrução de DOM/Footprint/Delta.
- **Replay/Reconstrução**: reconstrução de DOM/Footprint/Delta a partir de dados brutos; playback sincronizado.

## Padrões e Boas Práticas
- Normalização única (`MarketEvent`), desacoplamento de provedores/adaptadores.
- Telemetria por feed/adaptador: latência, quedas, contagem de eventos.
- Testes: mocks para cada feed/broker; datasets de replay específicos; validação de mapping cross-market.

## Roadmap Relacionado
- Fase VII–VIII (feeds profissionais, abstração multi-feed).
- Fase VI e VII (multi-broker execution, dual execution).
- Fase IX (reconstrução/replay avançados).
