# Status — Issue #248: option for not stopping in a cycle

- [ ] Done

## What's done

- Plan accepted; build on `248-cycle-no-stop`.
- Config key `cycle_onfail` (`stop`|`skip`, default `stop`) in `modes.py` /
  `config.py` / `config_ops.py` (env `ISSUEFLOW_CYCLE_ONFAIL`).
- Cycle skill + command bake `{{ cycle_onfail }}`; per-run `onfail:` token wins.
- Docs: `configuration.md`, `how-to/cycle.md`, `skill-behaviour-knobs.md`.
- Tests: resolve / invalid / env / templating bake / config_ops enum / modes
  write-default; full suite green (898), ruff clean.
- `issue-flow update` re-baked scaffold (cycle skill shows default `stop`).

## Remaining work

- `/iflow-close` (HISTORY, commit already in build if pushed, PR, Done checkbox).
