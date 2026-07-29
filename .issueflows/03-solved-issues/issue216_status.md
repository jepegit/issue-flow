# Status — Issue #216: possible bug in gitutils

- [x] Done

## What's done

- Plan accepted (`issue216_plan.md`).
- Branch `cursor/216-gitutils-bug-3d36` (from `main`).
- `gitutils._run`: UTF-8 decode + `errors="replace"`; None-safe `_stdout` / `_stream_text`.
- Templates: `iflow_cleanup` + `_resolve_project_root` teach positional `gh repo view`.
- Design notes: `gh-repo-view-positional.md`, updates to `agentic-cli.md` / `multi-repo-workspaces.md`.
- Tests: encoding kwargs + None-stdout paths (`tests/test_gitutils.py`); full suite 566 passed.
- Refreshed dogfood `.cursor/skills/*` via `issue-flow update`.
- PR: https://github.com/jepegit/issue-flow/pull/217 (#217, draft)

## Remaining work

- HISTORY / version bump / ready-for-review via `/iflow-close`.
