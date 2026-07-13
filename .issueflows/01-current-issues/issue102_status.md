# Issue #102 status: GitHub Actions sync

- [ ] Done

## What's done

- `src/issue_flow/sync.py` — scan `01`/`02`/`03`, plan label/milestone/close diffs, dry-run + apply
- `issue-flow sync` CLI (`--apply`, `--json`, `--repo`)
- `gitutils` — `gh_issue_edit`, `gh_issue_close`, `gh_milestone_titles`; `gh_issue_meta` includes milestone
- `[issueflow.sync]` config via `modes.read_sync_settings` + `load_sync_settings`
- Reusable workflow `.github/workflows/issue-flow-sync.yml` + dogfood caller `issueflow-sync.yml`
- README "GitHub Actions sync" section (removed from Future plans)
- Tests: `tests/test_sync.py` (8), CLI smoke in `test_cli.py`

## Remaining work

- [ ] `/iflow-close` — full suite already green (476 passed), version bump, PR

## Tests

- `uv run pytest tests/test_sync.py tests/test_cli.py::test_sync_help_documents_apply tests/test_cli.py::test_sync_json_dry_run` — 10 passed
- `uv run pytest` — 476 passed
- `uv run ruff check src/ tests/` — clean
