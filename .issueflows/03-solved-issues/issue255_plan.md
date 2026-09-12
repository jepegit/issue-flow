# Plan — Issue #255: Worktree + separate window on pick/issue start

## Goal

Start-work (`/iflow-pick`, `/iflow-issue` Phase 2, `/iflow-fix` branch create) puts the issue on a **sibling git worktree** and leaves the **home** checkout on the default branch. Capture/build/close run in that worktree. Cleanup removes the worktree before deleting the landed branch.

## Constraints

- Home checkout must not `git switch` onto `<N>-<slug>` (the cellpy bug).
- Capture writes uncommitted tracking files — must run **`-C <worktree>`**, not home (worktrees do not share the working tree).
- Git forbids two checkouts of the same branch: close **must not** `switchback` a worktree onto default while home already has it. Cleanup **must** `git worktree remove` **before** `git branch -d/-D`.
- No silent `--open` (same as #253). Ops may skip the worktree when the user stays on current/default.
- Opt-out token `inplace` / `no worktree` keeps today’s `git switch -c` on home. Worktree-add failure → **stop and ask**, never silent inplace fallback.
- Out of scope: sequential cycle worktrees; resolve/registry; headless force-open.

### Prior art

- `run_open_workspace` / `_resolve_open_workspace_target` — [`src/issue_flow/agent.py`](../../src/issue_flow/agent.py); print/`--open` only, **never** creates worktrees. Reuse after add.
- Parallel-cycle worktree recipe — [`iflow_cycle/SKILL.md.j2`](../../src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2), [`.issueflows/04-designs-and-guides/parallel-cycle.md`](../04-designs-and-guides/parallel-cycle.md), [`separate-workspaces.md`](../04-designs-and-guides/separate-workspaces.md) (#253). Mirror path `../<repo>-<N>`; start-work now uses the same layout for a single issue.
- `run_switchback` / `gitutils.switch_branch` — switches cwd onto default; **breaks** if cwd is a linked worktree and home already holds default. Must detect linked worktree and skip switch.
- `run_local_branches` — classifies locals; does not list/remove worktrees. Cleanup needs a worktree list + remove-before-delete.
- Pick/issue/fix Phase 2 — `git switch -c` on home ([`iflow_pick/SKILL.md.j2`](../../src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2) L69 and siblings). Replace with worktree-first.
- Toolbox: no worktree helper.

## Approach

1. **Thin CLI** `issue-flow agent worktree-add <N> --slug <slug> -C <home>` (and `worktree-list` / `worktree-remove <path-or-N>`):
   - Home: FF default if already on it (do **not** switch home off default unless already elsewhere and user confirmed — start-work requires home on default + clean, same gate as today).
   - Path: `<home.parent>/<home.name>-<N>` (same as cycle). Create branch from `origin/<default>` if missing, then `git worktree add <path> <N>-<slug>`.
   - Idempotent: existing worktree for that branch → return its path, `created: false`.
   - JSON: `path`, `branch`, `home_branch`, `home_path`, `created`, `error`. Never `--open`.
   - `worktree-remove`: refuse if worktree dirty or branch has unique unpushed work (caller still confirms). Used by cleanup after merge classify.

2. **Shared skill partial** `_worktree_start.md.j2` included by pick / issue / fix:
   - After the existing dirty-tree gate: `worktree-add` → `open-workspace <path> --json` → show path.
   - Fold “create worktree + optional `--open`” into the **existing** start confirm (one prompt). `inplace` skips worktree.
   - Then `/iflow-capture` with `-C <worktree>`. Tell the user to continue the session in that folder/window.

3. **Close / switchback** — if `git rev-parse --git-dir` ≠ `--git-common-dir` (linked worktree): **do not** switch to default. Set `switched: false`, note `in_worktree: true`. Yolo pull-on-default runs from **home** (`-C <home_path>`), not the worktree.

4. **Cleanup** — from home: `worktree-list`; for each issue worktree whose branch is in `reachable` / `squash_landed` / `merged_pr_divergent`, include `git worktree remove <path>` in Phase A1 (clean worktrees) / A2 (same buckets as `-D`). Then delete the branch. Never remove a worktree whose branch is `unique_work`.

5. **Docs** — update `separate-workspaces.md` (start-work vs parallel-only); pick/issue/fix/close/cleanup commands + workflow doc. Tests for add/idempotent/home-stays-default, switchback-skips-worktree, remove-before-delete.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/gitutils.py` | `worktree_add` / `list` / `remove` / `is_linked_worktree` |
| `src/issue_flow/agent.py` | `run_worktree_add` / `list` / `remove`; `run_switchback` skip on linked worktree |
| `src/issue_flow/cli.py` | `agent worktree-add` / `worktree-list` / `worktree-remove` |
| `src/issue_flow/templates/skills/_worktree_start.md.j2` | New shared start recipe |
| `src/issue_flow/templates/skills/iflow_{pick,issue,fix}/*.j2` + matching commands | Worktree-first Phase 2 |
| `src/issue_flow/templates/skills/iflow_{close,cleanup}/*.j2` + commands | Switchback skip; remove-before-delete |
| `.issueflows/04-designs-and-guides/separate-workspaces.md` | Start-work layout |
| `tests/test_*.py` | CLI + switchback + template markers |

## Test strategy

- `uv run pytest` — worktree-add keeps `-C` home on default; second add is idempotent; switchback on a fake linked worktree does not call `git switch`; worktree-remove refused when dirty.
- Template tests (like cycle/`open-workspace`): pick/issue/fix mention `worktree-add` and forbid silent `--open`; cleanup mentions `worktree remove` before `-D`.
- `uv run ruff check src/ tests/`.
- Manual: pick in a throwaway clone; `git -C <home> branch` still default; worktree path has `<N>-<slug>`.

## Open questions

1. **CLI vs skill-only `git worktree add`?** **Rec: thin CLI** — deterministic path, testable, cleanup can find/remove; skills still own confirm/`--open`.
2. **Config `worktree_on_start` (default true) plus `inplace` token?** **Rec: token only for v1** (`inplace` / `no worktree`); no new config key unless you want a permanent opt-out.
3. **Fold `--open` into the existing pick/issue confirm?** **Rec: yes** — one prompt: worktree path + “open window?”. Headless: decline open.
