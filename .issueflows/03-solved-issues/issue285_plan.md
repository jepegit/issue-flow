# Plan: #285 User-global config + precedence

## Goal

`config show --global` / `config set --global` work. Preference knobs
resolve project > user-global > env > default. Missing user file =
today’s behaviour.

## Approach

Add `user_global.py` (XDG / `%APPDATA%` path). Insert one layer in
`Settings.resolve_*` for preference knobs. Ignore `mode` / `locked` in
the user file. `--global` on `config show|set`. Isolate tests via
`XDG_CONFIG_HOME`. Docs in `docs/configuration.md`.

No lock persist, no registry, no `update --all` (those are #286 / #287).

## Files to touch

- `src/issue_flow/user_global.py` (new)
- `src/issue_flow/config.py`
- `src/issue_flow/cli.py` / `agent.py`
- `tests/conftest.py`, `tests/test_config_cli.py`
- `docs/configuration.md`

## Test strategy

Missing user file unchanged. Set global, project override, forbidden
`mode`. `uv run pytest`.
