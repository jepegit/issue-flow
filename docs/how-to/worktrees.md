---
title: Work in a sibling worktree (or stay inplace)
---

# Work in a sibling worktree (or stay inplace)

## Goal

Understand the default **worktree-first** start for `/iflow-pick`,
`/iflow-issue`, and `/iflow-fix`, how to **opt out for one run**, and
how to make inplace the **project default**.

Default is worktree-first (`worktree_first = true`). Set
`worktree_first = false` in `[issueflow]` (or `ISSUEFLOW_WORKTREE_FIRST=false`)
and re-run `issue-flow update` so start skills stay on home. Per-run tokens
still win.

## Default (worktree-first)

1. Home checkout stays on the **default** branch (`git fetch --prune`;
   `git pull --ff-only` only when home is not ahead of origin).
2. Agent creates a sibling worktree at `../<repo>-<N>` on branch
   `<N>-<slug>` via `issue-flow agent worktree-add` (from fetched
   `origin/<default>` — home does not need to be fast-forwardable).
3. It prints an `open-workspace` path (print-only). Skills do not open a
   new editor window.
4. Capture / plan / build / close run with `-C <worktree-path>`.
5. Close in a linked worktree does **not** switch that tree to default —
   pull default from **home**. After the PR is opened (or yolo-merged),
   close removes the sibling worktree when the tree is clean
   (`auto_remove_worktree`, default `true`; `false` asks YES/NO). Cleanup
   still removes leftover worktrees before deleting branches.

Use this when you want home free for other work, parallel agents, or a
clean default checkout while an issue is in progress.

## Project default (inplace)

```toml
[issueflow]
worktree_first = false
```

Then `issue-flow update`. Start skills run `git switch -c <N>-<slug>` on
home. Pass **`worktree`** on one run to still create `../<repo>-<N>`.

## Opt out for this run

Pass **`inplace`** or **`no worktree`** on the start command (forces home
even when `worktree_first` is true). Pass **`worktree`** to force a
sibling worktree when the knob is false:

```text
iflow pick inplace
iflow pick 42 no worktree
iflow issue inplace fix the login timeout
iflow fix inplace
iflow pick worktree
```

`inplace` / `no worktree` keep the legacy path: `git switch -c <N>-<slug>`
on **home**. No sibling folder; no separate window.

If home is already on a non-default branch, the agent asks whether to
FF/switch home to default first (needed for worktree-add) or use `inplace`
from the current branch.

## After the PR

`/iflow-close` removes the sibling worktree folder itself (see above).
Run `iflow cleanup` afterwards to prune the local **branch**. Cleanup
still removes any leftover worktree (reachable / squash-landed) **before**
`git branch -d` / `-D`. See [After a squash merge](after-squash-merge.md).

## Related

- [Work one issue end-to-end](work-one-issue.md) — pick → close loop
- [After a squash merge](after-squash-merge.md) — prune branches / worktrees
- [The workflow](../issue-workflow.md) — multi-root / worktree note
- [Use issue-flow in a folder of repos](workspaces.md) — parent folder + sibling repos (not the same as `../repo-N` worktrees)
- Design notes: [separate-workspaces.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/separate-workspaces.md)
  (issue-flow repository)
