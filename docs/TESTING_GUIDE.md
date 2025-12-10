# Testing Guide

## Camadas de Teste
- Unidade: engines (microstructure, estratégia, execução), observabilidade
- Integração: EventBus + pipeline de sinais/replay
- E2E (futuro): simulação com dados históricos

## Pytest
- Novos testes: `test_microstructure.py`, `test_strategy_orchestrator.py`, `test_smart_router.py`, `test_observability.py`
- Rodar: `python -m pytest`

## Fixtures
- EventBus para fluxos assíncronos
- SimAdapter para execução

## Critérios
- Determinismo: avoid sleep longo, usar thresholds determinísticos
- Cobertura: principais caminhos de cálculo e publicação no bus

## Observabilidade nos testes
- Logs JSON podem ser habilitados para troubleshooting
