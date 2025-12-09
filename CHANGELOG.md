# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
### Added
- Expanded pytest suite (EventBus, MarketEvent aliases, replay loader, IBKR mocking).
- Comprehensive documentation set (README, ARCHITECTURE, ROADMAP, CONTRIBUTING, STYLEGUIDE, DIAGRAMS).
### Changed
- EventBus made thread-safe with graceful shutdown and logging-friendly behavior.
- IBKR connector corrected for tick-by-tick signatures and fallback publishing.

## [v0.2.0] - 2025-12-09 (Fase II)
### Added
- IBKR normalization builders for tick-by-tick bid/ask, trades, DOM deltas, and Level 1 fallback.
- Historical replay loader for CSV/JSON with speed control.
- dxFeed provider placeholder for future adapter.
### Changed
- IBKR connector subscribes DOM depth and tick-by-tick feeds with automatic Level 1 fallback.

## [v0.1.0] - 2025-12-09 (Fase I)
### Added
- Canonical `MarketEvent` model.
- Initial `EventBus` implementation.
- Minimal IBKR connector bootstrap and example tests.
- Project dependencies and .gitignore baseline.
