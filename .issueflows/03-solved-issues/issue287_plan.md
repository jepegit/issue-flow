# Plan: #287 Registry + update-all

## Goal

`issue-flow update --all` refreshes every unlocked registered root.
Locked and missing roots are listed and skipped. No workspace file.

## Approach

Follow [user-global-config.md](../04-designs-and-guides/user-global-config.md).
`registry.toml` next to user-global config. `init` and `register` add
the resolved absolute root; `unregister` removes it. `update --all`
walks the list, skips missing/locked, runs `run_update` on the rest
(forward `--force` / `--editor` / `--skip-dep-check`), aggregates like
`workspace update`.

## Files to touch

- `src/issue_flow/user_global.py` — registry read/write
- `src/issue_flow/init.py` — register on init; `run_update_all`
- `src/issue_flow/cli.py` — `register` / `unregister` / `update --all`
- `tests/test_registry.py`
- `docs/cli.md`, `docs/configuration.md`

## Test strategy

Register + unregister; reject relative; init registers; update-all with
one locked, one unlocked, one missing tmp root.
