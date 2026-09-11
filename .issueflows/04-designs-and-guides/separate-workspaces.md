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
| Parallel cycle workers (`parallel:<n>`) | Separate window **per worktree** |
| Concurrent agents on sibling member repos | Separate window **per member** |
| Headless / CI / no GUI editor | Print path only — never force-open |
| Opt out of worktree on start | Token `inplace` / `no worktree` (legacy `git switch -c` on home) |

## Coordinator / worker split

- **Coordinator** stays in the parent (home) workspace: queue confirm, serial
  merges, `HISTORY.md` appends, worktree prune.
- **Workers** each get an isolated tree (`git worktree add …`) and, when the
  harness allows, their **own** editor window on that path.
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

# Launch only after an explicit confirm (skills must never auto-pass --open)
issue-flow agent open-workspace <worktree-path> --open
```

- **`worktree-add`:** path is `<home.parent>/<home.name>-<N>`. Idempotent if
  that branch already has a worktree. Capture/plan/build/close use
  `-C <worktree>`.
- **`open-workspace`:** print-only by default. `--open` is confirm-gated.
- **Close:** `agent switchback` in a linked worktree skips switching to
  default (`in_worktree: true`); pull default from **home**.
- **Cleanup:** `worktree-remove` **before** `git branch -d/-D`. Never remove a
  worktree whose branch is `unique_work`.

## Confirm-before-open

Skills that drive parallel work:

1. Create the worktree.
2. Run `open-workspace` **without** `--open` and show the path to the user.
3. Ask (or include in a consolidated confirm) before any `--open`.
4. If the harness cannot use separate windows, fall back to worktree-only
   parallel (existing background-exec gate) — separate windows are preferred,
   not a hard failure.

## Manual checklist

- [ ] `issue-flow agent open-workspace -C <repo> --json` returns `path` +
      `suggested_argv` with `opened: false`.
- [ ] Member name resolves under a workspace registry.
- [ ] `--open` without a binary on PATH exits non-zero and still prints the path.
- [ ] With Cursor installed, `--open` after confirm opens a new window (local only).
- [ ] Cycle skill text mentions print → confirm → `--open` (not silent spawn).

## Alternatives considered

- **Generate `.code-workspace` files per worktree** — deferred; opening a folder
  is enough for Cursor/VS Code in v1.
- **`issue-flow workspace open`** — rejected for v1; agents already use the
  `agent` surface (`resolve`, etc.). Registry lifecycle stays on `workspace`.
- **Always auto-open during `parallel:<n>`** — rejected; silent window spam and
  headless breakage.
