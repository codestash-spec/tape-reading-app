# ML_PIPELINES.md — Modelos de Microestrutura, Features e Pipelines

## Objetivo
Aplicar machine learning e modelos baseados em microestrutura para sinais, gestão de risco e execução, mantendo alinhamento operacional e thresholds seguros.

## Modelos e Padrões
- **Modelos baseados em microestrutura**: sequenciais (RNN/LSTM/Transformer), previsão de fluxo/imbalances, detecção de padrões (absorção, spoofing, bursts, failed breakout).
- **Pattern Detector**: biblioteca de regras/ML para padrões institucionais, com scoring e confiança.
- **Thresholds operacionais**: limites de score/confiança para acionar ordens ou alertas.

## Feature Engineering
- Features de fluxo: delta, CVD, Speed of Tape, imbalances bid/ask por nível/intervalo.
- Features de DOM: profundidade agregada, gaps, replenishment, spoofing (ordens inseridas/canceladas rapidamente).
- Features de footprint: volume por nível/agressor, point of control, distribuição de volume.
- Contexto: regimes de volatilidade, horário da sessão, proximidade a eventos.

## Dataset Builder
- Consolidação de eventos (tick/trade/DOM) em janelas; alinhamento temporal; etiquetas (labels) por padrão/sinal.
- Split train/val/test; normalização e imputação quando necessário.
- Armazenamento versionado de datasets; reprodutibilidade.

## Training Pipeline
- Pré-processamento: geração de features, balancing (se necessário), validação.
- Treino: modelos seqüenciais ou classificadores; avaliação em métricas operacionais (precisão/latência).
- Validação cruzada e teste em datasets de replay.
- Exportação de modelos e thresholds; versionamento de artefatos.

## Operação e Segurança
- Flags/feature toggles para ativar/desativar modelos em produção.
- Monitoramento de drift e degradação; métricas de acerto e latência.
- Fallback para sinais determinísticos caso modelo falhe ou degrade.

## Roadmap
- Fase XI: Modelos de microestrutura e pattern detection.
- Fase XI/IX: Dataset builder e pipelines de treino.
- Fase X: Risco governando thresholds e kill-switch para modelos.
