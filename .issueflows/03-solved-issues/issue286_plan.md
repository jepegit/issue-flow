# Plan: #286 Per-repo lock flag

## Goal

A repo can set `[issueflow] locked` and `config show` reports it. Default
unlocked. User-global `locked` ignored. `ISSUEFLOW_LOCKED` overrides for
one process.

## Approach

Follow [user-global-config.md](../04-designs-and-guides/user-global-config.md).
Same knob pattern as `fix_auto_name`: `DEFAULT_LOCKED` + `read_locked` +
`resolve_locked` (env first) + `CONFIG_KEYS` + seed / `write_default_config`
/ `effective_config`. Refuse `--global`.

## Files to touch

- `src/issue_flow/modes.py`, `config.py`, `config_ops.py` (already started)
- `tests/test_config.py`, `tests/test_config_cli.py`, `tests/test_modes.py`
- `docs/configuration.md`

## Test strategy

Seed + resolve defaults; persist via `config set`; `config show`;
`ISSUEFLOW_LOCKED` beats project; `--global locked` refused; user-global
file ignored.
