---
title: Work one issue end-to-end
---

# Work one issue end-to-end

## Goal

Take one GitHub issue from selection through a merged PR and local cleanup.

## Steps

1. **Pick** — in chat, type `iflow pick` (or `/iflow-pick`). Confirm the issue
   and branch / worktree.
2. **Plan** — `iflow plan`. Read the draft; reply **Accept** only when the
   approach is right. (With `auto_plan = true`, pick may chain here for you.)
3. **Build** — `iflow build`. Agent implements the confirmed plan.
4. **Close** — `iflow close`. Tests, optional changelog / version bump, commit,
   push, open PR.
5. **Merge** on GitHub (squash is the assumed default for this project).
6. **Cleanup** — `iflow cleanup`. Switch to the default branch, fast-forward,
   delete merged local branches behind confirms.

Forgot which step you are on? Type `iflow` — the dispatcher routes to capture,
plan, build, or close from the focus-issue files under `.issueflows/`.

## Related

- [The workflow](../issue-workflow.md) — full command reference
- [Getting started](../getting-started.md) — first-hour setup
- [Fast-track a small issue](yolo.md) — when the change is tiny
- [After a squash merge](after-squash-merge.md) — cleanup detail
