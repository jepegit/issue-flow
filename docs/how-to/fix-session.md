---
title: Run a fix session
---

# Run a fix session

## Goal

Knock out a bucket of small, unrelated fixes (typos, little bugs, polish) on
**one** branch and **one** PR, confirming each fix before it is made.

## Steps

1. From a clean default branch, run `iflow fix` (or `iflow fix <session name>`).
   The agent proposes one GitHub issue plus a branch `<N>-<slug>`; confirm
   once and it creates both, captures the issue, and starts an
   **Iterative fixes log** in `issue<N>_status.md`.
2. Describe the next fix, for example `iflow fix the README badge link is
   broken` (or just describe it in chat while the session is active).
3. The agent restates the fix, writes a short plan, and **waits for your yes**
   before touching code. Each confirmed fix is added to the log as a dated
   bullet.
4. Repeat step 2–3 as often as you like. If a "fix" turns out to be a real
   feature, the agent suggests splitting it into its own issue instead.
5. When you are done, run `iflow close`. It lands the whole session as one
   PR. Merge it, then `iflow cleanup`.

While a session is active, drive it with `iflow fix` and `iflow close`, not the
`iflow` dispatcher.

**Session names:** without a name the agent uses `iterative-small-fixes` (or
invents a slug when `fix_auto_name = true`).

## Related

- [Command reference](../issue-workflow.md) — `/iflow-fix`
- [Fast-track a small issue](yolo.md) — one small change, fully hands-off
- [Write a good issue](write-an-issue.md) — one well-defined deliverable instead
