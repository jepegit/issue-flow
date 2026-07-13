# Issue #23 — status

- [ ] Done

## What's done

- `materialize_surfaces` extracted to `src/issue_flow/surfaces.py`.
- Canonical store: `.issueflows/agent/skills/` + `manifest.json`.
- CLI: `issue-flow convert --to <editor|canonical>` (`--prune-other`, `--gitignore`).
- `issue-flow init --canonical` for team bootstrap.
- Config: `canonical_format`, persisted `editor` in `config.toml`.
- Tests: `tests/test_convert.py` (5 cases).
- Docs: `docs/configuration.md`, `multi-editor-conversion.md`.

## Remaining work

- Phase 2: opt-in git hooks for pull/push conversion (#23 step 5).
- Optional: extend `verify_scaffold.py` for convert round-trip smoke.
