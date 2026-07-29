# Issue #220 status

- [x] Done

## What's done

- Plan accepted (model-invoked `gh-ci` skill + pointers; keep #172 primacy).
- Added `src/issue_flow/templates/skills/gh_ci/SKILL.md.j2`.
- Registered `gh_ci` in `SKILL_DIRS`; excluded from lifecycle step profiles.
- Close skill/command: `gh run list` / `gh run watch` fallback + `gh-ci` pointer.
- Always-on rules + docs pointers; extended `gh-list-and-watch.md`.
- Tests updated (manifest counts, mode membership, render asserts).
- `uv run pytest` (579 passed) + `ruff check` clean.
- Re-ran `issue-flow update` so local `.cursor/skills/gh-ci` + managed blocks refresh.
- PR: https://github.com/jepegit/issue-flow/pull/225 (#225)
- HISTORY.md Unreleased bullet written; issue archived to `03-solved-issues/`.

## Remaining work

- None.
