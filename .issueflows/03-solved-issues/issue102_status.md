# Issue #102 status: GitHub Actions sync

- [x] Done

## Summary

Shipped `issue-flow sync` (dry-run + `--apply`), `[issueflow.sync]` config, reusable GitHub Actions workflow, dogfood caller on `main`, README docs, and tests. One-way folder → managed `status:*` labels; milestones and auto-close opt-in via config.

## What landed

- `src/issue_flow/sync.py` — scan `01`/`02`/`03`, plan label/milestone/close diffs
- `issue-flow sync` CLI (`--apply`, `--json`, `--repo`)
- `gitutils` — `gh_issue_edit`, `gh_issue_close`, `gh_milestone_titles`
- `.github/workflows/issue-flow-sync.yml` (reusable) + `issueflow-sync.yml` (dogfood)
- README "GitHub Actions sync" section
- `tests/test_sync.py` + CLI smoke tests

## Tests

- `uv run pytest` — 476 passed
- `uv run ruff check src/ tests/` — clean

## PR

- https://github.com/jepegit/issue-flow/pull/160
