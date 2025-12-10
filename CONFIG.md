# CONFIG.md — Sistema de Configuração

## Estrutura de `config/settings.yaml`
- `env`: ambiente lógico (dev/paper/prod).
- `symbols`: lista padrão de símbolos.
- `providers.ibkr.host|port|client_id`: endpoint IBKR.
- `telemetry.log_level`: nível de log.
- `execution.mode`: `sim` ou `ibkr`; `slippage_bps` opcional.
- `risk`: `symbols`, `max_size`, `max_exposure`, `throttle_max`, `collar_bps`.
- `replay.speed`: fator de velocidade para `HistoricalLoader`.

## Perfis (`config/profiles/{dev,paper,prod}.yaml`)
- **dev**: log DEBUG, modo sim.
- **paper**: modo sim por padrão; pode usar `mode=ibkr` com credenciais paper.
- **prod**: modo ibkr; log INFO.

Perfis são mesclados sobre o base quando `PROFILE` é definido.

## Overrides por Ambiente
- `ENV`, `PROFILE`
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID`
- `LOG_LEVEL`
- Outras chaves podem ser estendidas conforme loader.

## Segredos e Segurança
- `config/secrets.example.yaml` é exemplo; segredos reais via env/secret store.
- Nunca versionar credenciais; aplicar menor privilégio.

## Loader (`core/config.py`)
1. Carrega `settings.yaml`.
2. Aplica perfil (se `PROFILE` setado).
3. Aplica overrides de env.
4. Retorna `Settings` imutável para uso em runtime.
