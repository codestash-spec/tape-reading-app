# Style Guide

## Python conventions
- Target Python 3.11+; type hints are mandatory for public functions.
- Prefer dataclasses or Pydantic models for data structures; keep them immutable where possible.
- Pydantic v2: use `ConfigDict`, aliases for backward compatibility, and `extra="ignore"` for forward compatibility.
- Avoid `print`; use the standard `logging` module with contextual messages.
- Keep functions small and single-purpose; extract helpers for clarity.
- Handle exceptions explicitly and log actionable messages.

## Folder layout rules
- `core/` for infrastructure (EventBus, common utilities).
- `models/` for shared schemas (e.g., `MarketEvent`).
- `providers/` for data sources (IBKR, dxFeed, replay loaders).
- `ibkr/` for IBKR-specific adapters/normalizers.
- `tests/` mirrors the package layout with pytest fixtures in `tests/conftest.py`.

## Naming conventions
- **Engines**: `<domain>_engine.py` (e.g., `dom_engine`, `delta_engine`).
- **Providers**: `<provider>_provider.py` or `<provider>_connector.py`.
- **Events**: Use `event_type` strings in `snake_case` (`tick`, `dom_delta`, `trade`).
- **Topics**: EventBus subscriptions should match `event_type` values exactly.

## Logging
- Format: `"[Component] message"` or structured logging fields via the logging module.
- Include identifiers like `symbol`, `reqId`, or `client_id` in log lines for traceability.
- Avoid noisy logs inside tight loops; keep debug-level messages guarded.

## Module structure
- Group related code under packages mirroring domains (`core`, `ibkr`, `providers`, `engines`, `ui`).
- Keep pure functions (normalizers/builders) free of side effects and I/O.
- Tests should mirror package structure and prefer pytest fixtures for shared setup.
