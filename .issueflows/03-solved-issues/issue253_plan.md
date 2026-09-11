# Plan — Issue #253: Separate Cursor workspaces for parallel / multi-repo agent work

## Goal

Give agents a documented execution layout — **one editor workspace (window) per worktree / member repo** — plus a small confirm-gated CLI helper to print (and optionally launch) that path, wired into parallel-cycle guidance. Registry / resolve / serial merge stay as today.

## Constraints

- Back-compat: multi-root + `issueflow-workspace.toml` + `agent resolve` unchanged; this is an **execution layout**, not a new resolution mode.
- No silent auto-spawn of editor windows (CLI may expose `--open`; skills must confirm first; headless/CI never force-open).
- Parallel cycle: sequential default, harness gate, serial merges, HISTORY via coordinator — unchanged (#143).
- Templates are source of truth (`src/issue_flow/templates/`); dogfood via `issue-flow update` locally only if needed for verification.
- Out of scope: cross-repo parallel cycles; replacing multi-root; generating `.code-workspace` files (v1 opens/prints a folder path).

### Prior art

- `Workspace` / `load_workspace` / `discover_workspace` / `find_workspace_file` — [`src/issue_flow/project.py`](../../src/issue_flow/project.py) (community 23); registry only.
- `run_workspace_init` / `run_workspace_update` + `issue-flow workspace …` — [`src/issue_flow/agent.py`](../../src/issue_flow/agent.py), [`cli.py`](../../src/issue_flow/cli.py); no open/launch helper yet.
- Parallel dispatch (worktree-per-issue, no separate-workspace step) — [`iflow_cycle/SKILL.md.j2`](../../src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2), [`.issueflows/04-designs-and-guides/parallel-cycle.md`](../04-designs-and-guides/parallel-cycle.md).
- Multi-root resolution contract — [`multi-repo-workspaces.md`](../04-designs-and-guides/multi-repo-workspaces.md) (#67/#126).
- Toolbox: no existing open/launch helper (`00-tools/` — none relevant).
- Graph: workspace nodes are registry discovery only; no editor-launch edges.

## Approach

1. **Design doc** — Add `.issueflows/04-designs-and-guides/separate-workspaces.md` (durable; not overwritten by update):
   - When separate windows beat multi-root (parallel agents, rule/cwd isolation).
   - Coordinator = parent workspace; workers = one window each on their worktree/member path.
   - How this composes with multi-root registry + parallel-cycle worktrees.
   - Confirm-before-open rule; headless refusal.
   - Short pointer from `parallel-cycle.md` and `multi-repo-workspaces.md` (one short section or link each).

2. **CLI helper** — `issue-flow agent open-workspace [target]`:
   - **Resolve target:** absolute/relative path, or registry member name under discovered workspace; default = current `-C` / cwd project root.
   - **Always print JSON or human:** absolute path, suggested argv (editor binary from `shutil.which`: prefer configured editor / `cursor`, else `code` if present), and `would_open` / `binary_found`.
   - **`--open`:** only then `subprocess` launch (non-blocking); exit non-zero if binary missing. Default is **print-only**.
   - No git worktree create here — caller already has the path (cycle skill creates worktrees).

3. **Skills / docs templates** — Update parallel dispatch in `iflow_cycle` (+ command stub if needed) and `issue-workflow.md.j2` briefly:
   - After `git worktree add`, run `issue-flow agent open-workspace <worktree> --json` (print).
   - Ask user once (or include in the cycle’s consolidated confirm) before any `--open`.
   - If harness cannot use separate windows, still allow worktree-only parallel (existing gate); separate-workspace is preferred when available, not a hard fail beyond documenting fallback.

4. **Tests** — Unit tests for path/member resolution + print payload; `--open` mocked (never real spawn in CI). Manual checklist note in the design doc for a real Cursor launch.

## Files to touch

| Path | Change |
| --- | --- |
| `.issueflows/04-designs-and-guides/separate-workspaces.md` | New design guide |
| `.issueflows/04-designs-and-guides/parallel-cycle.md` | Link + one bullet: open each worktree as separate workspace |
| `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` | Link: when to prefer separate windows vs multi-root |
| `src/issue_flow/agent.py` | `run_open_workspace(...)` |
| `src/issue_flow/cli.py` | `agent open-workspace` command |
| `src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2` | Parallel dispatch: open-workspace step + confirm |
| `src/issue_flow/templates/commands/iflow-cycle.md.j2` | Brief mention if useful |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | One-line pointer under parallel / multi-repo |
| `tests/test_*.py` (new or extend) | Resolve + print + mocked `--open` |

## Test strategy

- `uv run pytest` (new/extended tests for `open-workspace`).
- `uv run ruff check src/ tests/`.
- Manual (optional, local): print path for a fake worktree dir; `--open` only if Cursor available — not required for CI green.

## Open questions

1. **CLI nesting:** Prefer `issue-flow agent open-workspace` (agent surface, like `resolve`) vs `issue-flow workspace open` (next to `workspace init/update`)? **Recommendation:** `agent open-workspace` — agents already look there; `workspace` stays registry lifecycle.
2. **Default editor binary:** Prefer `cursor` then `code`, or always the scaffolded `ISSUEFLOW_EDITOR` / config editor id mapped to a binary name? **Recommendation:** config/editor id → binary name (`cursor`→`cursor`, `claude`→best-effort), fall back to `cursor` then `code`; print-only still works with no binary.
3. **Cycle confirm:** Fold “open N worker windows” into the existing cycle consolidated confirm, or a second confirm right before `--open`? **Recommendation:** second confirm (or explicit “yes, open”) so print-only cycles stay quiet in headless.
