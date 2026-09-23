# Issue #329: Add a config knob to default to inplace (no sibling worktree)

Source: https://github.com/jepegit/issue-flow/issues/329

## Original issue text

## Problem / context

`/iflow-pick`, `/iflow-issue`, and `/iflow-fix` start worktree-first (`../<repo>-<N>`). The only opt-out is a per-run token (`inplace` / `no worktree`). Single-repo projects often want to stay on the home checkout. Typing the token every start is easy to forget, and there is no `[issueflow]` key for it (`auto_remove_worktree` only deletes the folder after close).

Related but distinct from #328 (worktree *location*). Docs already state there is no `config.toml` switch (`docs/how-to/worktrees.md`).

## Spec

- Add a project (and user-global) knob, defaulting to today’s worktree-first behaviour. Suggested shape:

```toml
[issueflow]
worktree_first = true   # false → start skills behave as inplace
```

- Bake it into pick / issue / fix on `issue-flow update`.
- Per-run tokens still win: `inplace` / `no worktree` force home; add an inverse (`worktree`) so a project default of `false` can still create a worktree once.
- `issue-flow config show` / `config set` / `config add` include the key; document it in `docs/how-to/worktrees.md` and the configuration page.

## Acceptance criteria

- Default unchanged: no config file still creates `../<repo>-<N>`.
- `worktree_first = false` (or equivalent) → `git switch -c <N>-<slug>` on home; no `worktree-add`.
- Per-run tokens override the knob.
- Docs and config help list the key.

## Out of scope

- Worktree *location* (#328).
- `/iflow-cycle` parallel worktrees.
- `auto_remove_worktree`.
