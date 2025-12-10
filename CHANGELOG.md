# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2025-12-10
### Added
- Engines DOM/Delta/Tape/Footprint em memória.
- Estratégia event-driven emitindo sinais e pipeline risco→execução.
- Execution Router com adaptadores sim e stub IBKR; eventos de ordem no EventBus.
- Telemetria estruturada (JSON logging, métricas/tracing helpers, audit line).
- Configuração com perfis (dev/paper/prod) e overrides por ambiente.
- Documentação completa Phase III (arquitetura, sinal, execução, ops, gov/sec).

### Changed
- README e ROADMAP atualizados para Fase III concluída.
- Arquitetura expandida para incluir risco e execução no fluxo principal.

### Fixed
- Remoção de referências e TODOs pendentes; clarificação de placeholders dxFeed.

## [0.2.0] - 2025-12-09 (Fase II)
### Added
- Normalizadores IBKR (tick-by-tick, DOM delta, fallback L1).
- Historical replay (CSV/JSON) com controle de velocidade.
- Placeholder dxFeed.

### Changed
- Conector IBKR assina DOM e tick-by-tick com fallback automático.

## [0.1.0] - 2025-12-09 (Fase I)
### Added
- `MarketEvent` canônico.
- `EventBus` thread-safe.
- Bootstrap IBKR mínimo e testes iniciais.
- Dependências e .gitignore base.
