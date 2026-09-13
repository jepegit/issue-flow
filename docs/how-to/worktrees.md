---
title: Work in a sibling worktree (or stay inplace)
---

# Work in a sibling worktree (or stay inplace)

## Goal

Understand the default **worktree-first** start for `/iflow-pick`,
`/iflow-issue`, and `/iflow-fix`, and how to **opt out for one run** so the
issue branch is created on the home checkout instead.

There is **no** `config.toml` switch for this — worktree-first is skill
default. Session opt-out is a trailing token.

## Default (worktree-first)

1. Home checkout stays on the **default** branch (`git pull --ff-only`).
2. Agent creates a sibling worktree at `../<repo>-<N>` on branch
   `<N>-<slug>` via `issue-flow agent worktree-add`.
3. It prints an `open-workspace` suggestion; opens a new editor window only
   after you confirm (`--open` is never silent).
4. Capture / plan / build / close run with `-C <worktree-path>`.
5. Close in a linked worktree does **not** switch that tree to default —
   pull default from **home**. Cleanup removes reachable worktrees before
   deleting branches.

Use this when you want home free for other work, parallel agents, or a
clean default checkout while an issue is in progress.

## Opt out for this run

Pass **`inplace`** or **`no worktree`** on the start command:

```text
iflow pick inplace
iflow pick 42 no worktree
iflow issue inplace fix the login timeout
iflow fix inplace
```

That keeps the legacy path: `git switch -c <N>-<slug>` on **home**. No
sibling folder; no separate window.

If home is already on a non-default branch, the agent asks whether to
FF/switch home to default first (needed for worktree-add) or use `inplace`
from the current branch.

## After the PR merges

Run `iflow cleanup` as usual. For worktree-backed branches it removes the
linked worktree (when the branch is reachable / squash-landed) **before**
`git branch -d` / `-D`. See [After a squash merge](after-squash-merge.md).

## Related

- [Work one issue end-to-end](work-one-issue.md) — pick → close loop
- [After a squash merge](after-squash-merge.md) — prune branches / worktrees
- [The workflow](../issue-workflow.md) — multi-root / worktree note
- Design depth (agents): `.issueflows/04-designs-and-guides/separate-workspaces.md`
  after `issue-flow init`
