# Issue #253 — status

- [ ] Done

## What's done

- Design doc `.issueflows/04-designs-and-guides/separate-workspaces.md`; links from `parallel-cycle.md` + `multi-repo-workspaces.md`.
- CLI `issue-flow agent open-workspace` — print-only default, optional `--open`, member/path resolve, JSON payload.
- Templates: `iflow_cycle` skill, `iflow-cycle` command, `issue-workflow.md` parallel/multi-repo notes.
- Tests: five `open-workspace` CLI cases + cycle skill asserts `open-workspace` / `--open` / design doc ref.
- `uv run pytest` (702 passed), `uv run ruff check src/ tests/` clean.

## Remaining work

- `/iflow-close` (changelog, commit, PR). Optional: `issue-flow update` in this repo to refresh local skills from templates.
