# Status — Issue #163: How to handle branches on GitHub

- [ ] Done

## What's done

- Plan accepted (recommended defaults).
- `gitutils` remote audit helpers: `list_origin_branches`, `cherry_unique_count`, `unique_commit_onelines`, `unique_diff_shortstat`, `gh_prs_for_head`, `branch_is_protected`.
- `issue-flow agent branches [--json] [--no-fetch] [--commit-limit N]` (read-only classification).
- `/iflow-cleanup` skill + command: Phase B tokens (`include github` / …), second confirm for remote delete + findings issue.
- Workflow doc + rules body mention; design doc `github-branch-audit.md`.
- Tests (gitutils / cli / templating); full suite green; `issue-flow update` dogfood (incl. prune `iflow-start` → `iflow-build`).

## Remaining work

- `/iflow-close` (tests already green; optional version bump / HISTORY / PR finalize).
