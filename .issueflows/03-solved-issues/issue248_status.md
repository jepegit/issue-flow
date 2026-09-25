# Status — Issue #248: option for not stopping in a cycle

- [x] Done

## What's done

- Config key `cycle_onfail` (`stop`|`skip`, default `stop`) in `modes.py` /
  `config.py` / `config_ops.py` (env `ISSUEFLOW_CYCLE_ONFAIL`).
- Cycle skill + command bake `{{ cycle_onfail }}`; per-run `onfail:` token wins.
- Docs: `configuration.md`, `how-to/cycle.md`, `skill-behaviour-knobs.md`.
- Tests: resolve / invalid / env / templating bake / config_ops enum / modes
  read-default; full suite green (898), essential (18), ruff clean.
- `issue-flow update` re-baked scaffold.
- Version bump `0.5.11` → `0.5.12`; HISTORY promoted.

## Essential tests review

- Touched: `test_config` / `test_config_cli` / `test_templating` /
  `test_modes` / `test_cli` asserts — leave unmarked (config/template
  unit coverage; not hot-path essential).
- Registry: one row for `test_cycle_bakes_onfail_default` (not essential).

## Remaining work

- None (close / PR).
