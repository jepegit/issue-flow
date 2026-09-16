# Separate editor workspaces (execution layout)

Context: issue #253 — parallel agents and multi-repo work often share one
multi-root Cursor window. Shared context mixes rules, cwd, and
`agent resolve` signals. Prefer **one editor workspace (window) per active
worktree / member repo** when concurrent agent runs matter.

This is an **execution layout**, not a replacement for the multi-repo registry
(`issueflow-workspace.toml`) or `issue-flow agent resolve`. Those stay the
source of truth for *which* repo a command targets.

## When to use separate windows

| Situation | Prefer |
| --- | --- |
| One human, one focus repo, light sibling glance | Multi-root (see [multi-repo-workspaces.md](./multi-repo-workspaces.md)) |
| `/iflow-pick` / `/iflow-issue` / `/iflow-fix` start (#255) | Sibling worktree `../<repo>-<N>`; home stays on default |
| Parallel cycle workers (`parallel:<n>`) | Isolated worktree **per issue** (print path; no skill-launched window) |
| Concurrent agents on sibling member repos | Isolated worktree / member folder (print path) |
| Headless / CI / no GUI editor | Print path only |
| Opt out of worktree on start | Token `inplace` / `no worktree` (legacy `git switch -c` on home) |

## Coordinator / worker split

- **Coordinator** stays in the parent (home) workspace: queue confirm, serial
  merges, `HISTORY.md` appends, worktree prune.
- **Workers** each get an isolated tree (`git worktree add …`). Skills print
  the path; they do not launch a window (issue #273).
- Serial merge + HISTORY-via-coordinator rules from
  [parallel-cycle.md](./parallel-cycle.md) are unchanged.

## CLI helper

```bash
# Create ../<repo>-<N> on <N>-<slug>; home checkout is not switched
issue-flow agent worktree-add <N> --slug <slug> -C <home> --json

issue-flow agent worktree-list -C <home> --json
issue-flow agent worktree-remove <path-or-N> -C <home> --json

# Print path + suggested launch argv (default — safe everywhere)
issue-flow agent open-workspace [<path-or-member>] -C <start> --json

# Manual escape hatch only — skills never pass --open (issue #273)
issue-flow agent open-workspace <worktree-path> --open
```

- **`worktree-add`:** path is `<home.parent>/<home.name>-<N>`. Idempotent if
  that branch already has a worktree. Capture/plan/build/close use
  `-C <worktree>`.
- **`open-workspace`:** print-only by default. Skills never pass `--open`.
  The flag remains a manual CLI escape hatch.
- **Close:** `agent switchback` in a linked worktree skips switching to
  default (`in_worktree: true`); pull default from **home**. Then
  `worktree-remove` when `auto_remove_worktree` is on (or after YES).
- **Cleanup:** leftover `worktree-remove` **before** `git branch -d/-D`. Never
  remove a worktree whose branch is `unique_work`.

## Print-only (skills)

Skills that start or parallelize work:

1. Create the worktree.
2. Run `open-workspace` **without** `--open` and show the path to the user.
3. Do **not** ask to launch a window. Continue in the current session with
   `-C <worktree>`.

## Manual checklist

- [ ] `issue-flow agent open-workspace -C <repo> --json` returns `path` +
      `suggested_argv` with `opened: false`.
- [ ] Member name resolves under a workspace registry.
- [ ] Start skills (pick / issue / fix / cycle) never mention `--open`.
- [ ] Close skill mentions `worktree-remove` gated by `auto_remove_worktree`.

## Alternatives considered

- **Generate `.code-workspace` files per worktree** — deferred; opening a folder
  is enough for Cursor/VS Code in v1.
- **`issue-flow workspace open`** — rejected for v1; agents already use the
  `agent` surface (`resolve`, etc.). Registry lifecycle stays on `workspace`.
- **Always auto-open during `parallel:<n>`** — rejected; silent window spam and
  headless breakage.
