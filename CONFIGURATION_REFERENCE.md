# CONFIGURATION_REFERENCE.md — Referência de Configuração

## Arquivos de Configuração
- `config/settings.yaml`: base para todos os ambientes.
- `config/profiles/dev.yaml`: modo sim, log DEBUG.
- `config/profiles/paper.yaml`: modo sim (ou ibkr com credenciais paper), log INFO.
- `config/profiles/prod.yaml`: modo ibkr, log INFO.
- `config/secrets.example.yaml`: exemplo de segredos (não versionar segredos reais).

## Chaves de `settings.yaml`
- `env`: dev/paper/prod.
- `symbols`: lista padrão.
- `providers.ibkr.host|port|client_id`: endpoint IBKR.
- `telemetry.log_level`: nível de log.
- `execution.mode`: `sim` ou `ibkr`; `slippage_bps` opcional.
- `risk`: `symbols`, `max_size`, `max_exposure`, `throttle_max`, `collar_bps`.
- `replay.speed`: fator de velocidade para `HistoricalLoader`.

## Overrides via Ambiente
- `PROFILE`: seleciona perfil (dev/paper/prod).
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID`.
- `LOG_LEVEL`.
- Outros podem ser adicionados conforme necessidade, convertidos no loader.

## Loader (`core/config.py`)
- Carrega base.
- Aplica perfil (se `PROFILE`).
- Aplica overrides de env.
- Retorna `Settings` imutável (dataclass) para consumo runtime.

## Recomendações Operacionais
- Manter configs versionadas; segredos separados.
- Validar perfis em ambiente dedicado antes de produção.
- Em produção, injetar via env/secret store; evitar editar arquivos em runtime.

## Exemplo de Execução
```
PROFILE=dev LOG_LEVEL=DEBUG python main.py --mode sim
PROFILE=prod IBKR_HOST=127.0.0.1 IBKR_PORT=7497 python main.py --mode ibkr --symbol XAUUSD
```
