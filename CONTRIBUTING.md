# Contributing

## Ground rules
- Use Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`).
- Keep changes scoped and focused; prefer small, reviewable PRs.
- Add/adjust tests for any behavior change; keep coverage for core flows.

## Branch naming
- `feature/<short-desc>` for new functionality.
- `fix/<short-desc>` for bug fixes.
- `chore/<short-desc>` for maintenance or docs.
- `experiment/<short-desc>` for spikes/prototypes.

## Pull request workflow
1. Branch from `main` and rebase frequently.
2. Run `pytest` locally; include new tests/fixtures where relevant.
3. Update docs/diagrams if the architecture or flows change.
4. Open a PR with a clear summary, risks, and test evidence.
5. Address review comments with follow-up commits (do not force-push shared branches).

## Code review expectations
- Validate correctness, thread-safety, and error handling.
- Enforce logging best practices (no `print`, prefer `logging` with context).
- Ensure normalization contracts stay stable (`MarketEvent` fields).
- Check for backward compatibility of public APIs and configuration knobs.
- Require tests for new behavior and verify flaky tests are handled (timeouts, deterministic data).

## Repo hygiene
- Never commit virtualenvs, DLLs, datasets, or other large/binary artifacts (`.venv/`, `*.dll`, `data/` etc.).
- Keep `.gitignore` in sync when adding new tooling or generated assets.
