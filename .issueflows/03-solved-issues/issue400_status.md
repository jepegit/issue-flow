# Issue #400 status

- [x] Done

## What's done

- Captured #400 on branch `400-graphify-gitignore`.
- `graphify_gitignored` (default false) gitignores all of `graphify-out/` on `init` / `update` and makes `/iflow-plan` and epic draft run `issue-flow graphify` first. `auto_graphify_on_plan` still refreshes when the report is committed. Update prints `git rm -r --cached graphify-out` and does not run it.
- This repo's knob stays off, so `GRAPH_REPORT.md` stays tracked.
- Changelog bullet under `## [Unreleased]`. No version bump (no `publish` label).
- Essential review: new tests left unmarked (temp git / text contracts). `test_all_settings_table_lists_every_config_key_once` stays essential and covers the new config row. Registry updated.
- `uv run pytest`: 959 passed. `uv run pytest -m essential`: 24 passed. Ruff clean.

## Remaining work

- None.
