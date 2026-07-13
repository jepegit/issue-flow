# Issue #23 — status

- [x] Done

## What's done

- `materialize_surfaces` extracted to `src/issue_flow/surfaces.py`.
- Canonical store: `.issueflows/agent/skills/` + `manifest.json`.
- CLI: `issue-flow convert --to <editor|canonical>` (`--prune-other`, `--gitignore`).
- `issue-flow init --canonical` for team bootstrap.
- Config: `canonical_format`, persisted `editor` in `config.toml`.
- Tests: `tests/test_convert.py` (5 cases).
- Docs: `docs/configuration.md`, `multi-editor-conversion.md`.
- CI fix: shared `console_io` for `workspace update --json`.
- Landed in PR #161 (squash-merged 2026-07-13).

## Remaining work

- None for the confirmed Phase 1 scope. Git hooks (issue step 5) deferred to follow-up (#101-adjacent / new issue).
