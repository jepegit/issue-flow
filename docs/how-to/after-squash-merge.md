---
title: After a squash merge
---

# After a squash merge

## Goal

After the PR merges (squash), get back on the default branch and delete stale
local issue branches safely.

## Steps

1. Confirm the PR is merged on GitHub.
2. Run `iflow cleanup` (or `/iflow-cleanup`).
3. Under one confirm: switch to default, `git pull --ff-only`, `git fetch --prune`,
   and `git branch -d` on locals that are reachable from default.
4. Squash-landed branches often fail `-d` (unreachable tip). Cleanup offers a
   **second** confirm listing tip SHAs for `git branch -D` — only those tips;
   branches with unique work are never deleted.
5. Optional: trailing `include GitHub` audits remote branches (further confirm
   before any remote delete).

Close / yolo / cycle **remind** you to run cleanup; they do not run it for you.

## Related

- [The workflow](../issue-workflow.md) — `/iflow-cleanup`
- [CLI](../cli.md) — `agent local-branches` / `agent branches` (read-only audits)
- [Refresh dirty open PRs](pr-sync.md) — when other open PRs went dirty
