# Status — Issue #218: doctor leftovers

- [x] Done

## What's done

- Plan accepted.
- `gitutils.issueflows_only_dirty` + `dirty_paths` rename expansion (both sides).
- `agent preflight --json` now reports `dirty_paths` + `issueflows_only`.
- `/iflow-doctor` + `/iflow-pick` templates (skill + command): issueflows-only
  dirty → default housekeeping commit (one confirm, no push, no CLI auto-commit).
- `dirty-issueflows.md` post-repair section; issue-workflow + `docs/cli.md` wording.
- Dogfood: `uv tool install --force --editable .` + `issue-flow update`.
- Tests: 572 passed; ruff clean.
- HISTORY Unreleased bullet.
- PR: https://github.com/jepegit/issue-flow/pull/222 (#222)

## Remaining work

- None.
