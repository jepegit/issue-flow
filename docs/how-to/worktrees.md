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
2. Agent creates a worktree on branch `<N>-<slug>` via
   `issue-flow agent worktree-add` (from fetched `origin/<default>` — home
   does not need to be fast-forwardable). It is a sibling folder
   `../<repo>-<N>` unless you set a common folder; see
   [Where the worktree goes](#where-the-worktree-goes).
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

## Where the worktree goes

By default the worktree is a sibling of your repo: `../<repo>-<N>`. Two
settings change that:

| Situation | Worktree goes to |
| --- | --- |
| The repo is inside a workspace folder (an `issueflow-workspace.toml` above it) and `worktrees_in_workspace = true` (default) | `../<repo>-<N>`, inside the workspace folder |
| `worktrees_dir` is set and that folder exists | `<worktrees_dir>/<repo>-<N>` |
| `worktrees_dir` is set but the folder is missing, or the path is relative | `../<repo>-<N>`, with a note saying why |
| Nothing set | `../<repo>-<N>` |

For stand-alone repos, a common folder keeps your projects folder tidy.
Create it once and set it for your whole machine:

```bash
mkdir -p ~/worktrees
issue-flow config set --global worktrees_dir ~/worktrees
```

Repos in a workspace folder (such as `cellpy-workspace/` holding `cellpy`,
`cellpy-core`, …) still keep their worktrees in that folder. Set
`worktrees_in_workspace = false` to send those to `worktrees_dir` too.
`issue-flow agent worktree-add` reports which rule applied in its
`location` field (`sibling`, `workspace`, `worktrees_dir`, or `fallback`).
A project can switch a user-wide folder off with `worktrees_dir = ""` in its
own `config.toml`.

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
- [Command reference](../issue-workflow.md) — `/iflow-pick` worktree start
- [Use issue-flow in a folder of repos](workspaces.md) — parent folder + sibling repos (not the same as `../repo-N` worktrees)
- Design notes: [separate-workspaces.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/separate-workspaces.md)
  (issue-flow repository)
