# Status — Issue #216: possible bug in gitutils

- [ ] Done

## What's done

- Plan accepted (`issue216_plan.md`).
- Branch `216-gitutils-bug` from `main`.
- `gitutils._run`: UTF-8 decode + `errors="replace"`; None-safe `_stdout` / `_stream_text`.
- Templates: `iflow_cleanup` + `_resolve_project_root` teach positional `gh repo view`.
- Design notes: `gh-repo-view-positional.md`, updates to `agentic-cli.md` / `multi-repo-workspaces.md`.
- Tests: encoding kwargs + None-stdout paths (`tests/test_gitutils.py` — 32 passed).
- Refreshed dogfood `.cursor/skills/*` via `issue-flow update`.

## Remaining work

- HISTORY / version bump / PR close via `/iflow-close`.
