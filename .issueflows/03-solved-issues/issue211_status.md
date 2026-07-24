# Status: #211 — option C problem

- [x] Done

## What's done

- Plan confirmed: unify all leftover `agent` cmds onto `-C` / `--project-dir`.
- Added `_PROJECT_DIR_OPTION` in `cli.py`; migrated `audit`, `repair`, `state`,
  `preflight`, `switchback`, `branches`, `version-plan`, `sweep`.
- Tests updated to `-C`; regression test for sweep `-C` (#211 recipe).
- `docs/cli.md` synopsis + `agentic-cli.md` constraint note.
- `uv run pytest` — 563 passed; ruff clean.
- Smoke: `agent sweep --except 211 -C /workspace --dry-run --json` exits 0.
- Version bump `0.4.6` → `0.4.7`; HISTORY promoted.
- Draft PR: https://github.com/jepegit/issue-flow/pull/212 (#212)

## Remaining work

- None.
