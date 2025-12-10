# OPERATIONS_RUNBOOK.md — Operação e Recuperação

## Modos de Operação
- **SIM**: `python main.py --profile dev --mode sim`
- **LIVE IBKR**: `python main.py --profile prod --mode ibkr --symbol XAUUSD --host 127.0.0.1 --port 7497` (TWS/IB Gateway ativo, permissões).
- **REPLAY**: `python run_replay.py --file data/events.json --speed 2.0`

## Monitoramento
- Logs JSON em stdout; filtrar por `component`, `symbol`, `order_id`.
- Métricas in-memory; exportar snapshot conforme necessário.
- Tracing: usar `trace_id`/`span_id` para correlação ponta-a-ponta.

## Kill-switch
- Ativar `risk_engine.kill_switch_engaged = True` ou `KillSwitch.engage()`.
- Cancelar ordens ativas (IBKR via gateway; sim é imediato).
- Registrar acionamento em audit/log.

## Recuperação de Falhas
- Feed estagnado: fallback L1, suspender estratégia, verificar IBKR.
- Execução falha: kill-switch, cancel, possível migração temporária para sim.
- Reinício: parar `EventBus`, reiniciar processo, validar config/perfil e credenciais.

## Papéis
- Operador: inicia/paralisa modos, monitora, aciona kill-switch.
- Desenvolvedor: atua em sim/replay.
- Auditor: revisa logs/audit.

## Passos Rápidos
1) Definir `PROFILE` e envs (host/port/client_id/log level).
2) Garantir TWS/IB Gateway (live) ou isolamento (sim/replay).
3) Executar comando do modo escolhido.
4) Monitorar logs iniciais de conexão/publicação.
5) Em incidente: kill-switch, cancela, registra, só retomar após análise.
