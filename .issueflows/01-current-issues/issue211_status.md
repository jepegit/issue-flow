# Status: #211 — option C problem

- [ ] Done

## What's done

- Plan confirmed: unify all leftover `agent` cmds onto `-C` / `--project-dir`.
- Added `_PROJECT_DIR_OPTION` in `cli.py`; migrated `audit`, `repair`, `state`,
  `preflight`, `switchback`, `branches`, `version-plan`, `sweep`.
- Tests updated to `-C`; regression test for sweep `-C` (#211 recipe).
- `docs/cli.md` synopsis + `agentic-cli.md` constraint note.

## Remaining work

- Full `uv run pytest` + smoke `agent sweep -C`.
- `/iflow-close` when green.
