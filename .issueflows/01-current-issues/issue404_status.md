# Status — issue #404

- [ ] Done

## What's done

- Captured the issue and confirmed the plan (whole issue, trailers, `changelog release` writes `HISTORY.md` only).
- Branch `404-changelog-trailers` in worktree `/workspace-404`.
- `changelog list` / `release` / `check` read commit trailers and prepend one version section on the default branch.
- Close templates emit trailers and do not stage `HISTORY.md`. `defer_changelog` no longer selects a write path.
- Docs, design notes, and a pull-request CI check. `uv run pytest` and `uv run ruff check src/ tests/` passed.

## Remaining work

- `/iflow-close` (tests already green; changelog bullet belongs in the commit message, not in `HISTORY.md`).
