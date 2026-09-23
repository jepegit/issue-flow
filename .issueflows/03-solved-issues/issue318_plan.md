# Plan: #318 workspace-wide actions

## Goal

Give agents a **workspace fan-out** for the commands people actually want to
run on every member (`status`, `doctor`, `cleanup`) plus a **safe way to land
scaffold dirt** after `workspace update` — without a parent `.issueflows/` or
silent git writes.

## Constraints

- Per-repo tracker stays. No workspace-root `.issueflows/`.
- One member failure does not abort the rest (same as `workspace update`).
- Skip missing / non-scaffolded / **locked** members; list them.
- Never auto-dispatch `/iflow-pick` / `/iflow-yolo` / close from fan-out.
- `doctor --fix` and cleanup deletes stay **gated** (per-repo confirm).
- Default-branch hygiene (#303): do not leave unpushed commits on home `main`.
- Honour existing resolve order; fan-out only when the user asked for
  workspace scope (`workspace <cmd>` or trailing `workspace` / `all`).

### Prior art

- `project.discover_workspace` / `Workspace.member_roots` /
  `unique_resolved_paths` — registry walk (`src/issue_flow/project.py`).
- `run_workspace_update` — per-member loop, continue-on-fail, `--json`
  aggregate (`src/issue_flow/agent.py`). Extract the member-pair walk; do
  not copy-paste a third loop.
- `run_update_all(..., include_workspace=True)` — registry ∪ workspace
  (#296). Do **not** mix registry roots into `workspace status|doctor`;
  those stay workspace-file members only.
- `run_status` / `run_audit` / `run_repair` — per-root engines to call
  with each member path.
- Design doc already names this: “Multi-repo status dashboard —
  `issue-flow status --workspace`” as Phase 4 / out of scope in
  [multi-repo-workspaces.md](../04-designs-and-guides/multi-repo-workspaces.md).
  Prefer **`issue-flow workspace status`** (subcommand next to `update`)
  over a flag on the single-repo `status` command — keeps `-C` / positional
  `project_dir` unambiguous.
- `/iflow-cleanup` already says: if `sibling_roots`, repeat per repo; do
  not loop automatically. This issue **adds an opt-in loop**, not a silent
  one.
- Toolbox: no helper for fan-out. Reuse CLI, no new `00-tools/` script.

## Approach

### 1. Shared member walk

Add `iter_workspace_members(start) -> tuple[Workspace, list[tuple[str, Path]]]`
(or equivalent) next to `discover_workspace`. Dedupes by resolved path.
`run_workspace_update` switches to it.

### 2. CLI — read / audit (this PR)

| Command | Behaviour |
|---|---|
| `issue-flow workspace status [--local] [--json]` | `run_status` per member. Text: one summary line each. JSON: `{workspace_root, members:[{name,path,...status}]}`. Exit 1 if any member call fails. |
| `issue-flow workspace doctor [--json]` | `run_audit` per member. Aggregate findings with `member` on each row. **No `--fix`.** |

Missing workspace file → same error as `workspace update`.

### 3. CLI — post-update dirt (this PR, no write)

`issue-flow workspace dirty [--json]` — `git status --porcelain` per member.
Classify `clean` / `issueflows_only` / `mixed` (reuse preflight’s rule).
Agents use this after `workspace update` instead of guessing cwd.

**No auto-commit / auto-push in this PR.** Landing is: agent reads `dirty`,
then per dirty member follows existing close/housekeeping rules (chore
branch if on default). A `workspace land` / `--commit --push` command is a
follow-up (Open questions).

### 4. Skills / docs

- `/iflow-status`: if trailing `workspace` / `all` **or** cwd is the
  workspace root (toml present, not a member), run `workspace status`.
  Else keep single-repo.
- `/iflow-doctor`: same for `workspace doctor`. Repair: still
  `doctor --fix -C <member>` after the user names members.
- `/iflow-cleanup`: trailing `workspace` / `all` / `include workspace` —
  **opt-in sequential loop**. One up-front confirm listing member names.
  Then the existing Phase A1/A2 (and optional B) **per member**. Stop the
  whole walk only on user abort; a declined A2 in one repo continues to
  the next. Do not invent a mute `workspace cleanup` CLI.
- How-to + CLI glance tables + `multi-repo-workspaces.md`: promote Phase 4
  from “out of scope” to shipped; mention cleanup token and `workspace dirty`.

### 5. Out of scope (this PR)

- Fan-out of pick / plan / build / close / cycle / yolo.
- `doctor --fix` across all members in one shot.
- Auto merge+push after `workspace update`.
- Registry `--all` mixed into these commands.

## Files to touch

- `src/issue_flow/project.py` — `iter_workspace_members`
- `src/issue_flow/agent.py` — `run_workspace_status` / `_doctor` / `_dirty`;
  switch `run_workspace_update` onto the helper
- `src/issue_flow/cli.py` — three `workspace` subcommands
- `tests/test_workspace_actions.py` (new) — two-member tmp workspace:
  status/doctor/dirty JSON shape; missing toml errors; locked skip;
  continue-on-fail
- `tests/test_project.py` — helper unit if not covered above
- Templates: `iflow_status`, `iflow_doctor`, `iflow_cleanup` (+ command
  mirrors)
- `docs/how-to/workspaces.md`, `docs/cli.md`,
  `.issueflows/04-designs-and-guides/multi-repo-workspaces.md`

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/`.

New tests use `tmp_path` + two stub `.issueflows/` members + a toml
(no live `gh`). Stub `run_status` / `run_audit` / porcelain if needed so
CI stays offline. One test: member B raises → member A still in payload,
exit 1.

## Open questions

1. **Land after update** — comment asked for merge+push of workspace-update
   dirt. This plan reports dirt only. Ship `workspace land` (confirm +
   chore-branch commits, never push default) **in this PR**, or file a
   follow-up?
   - **Recommended:** follow-up. Writes-across-repos need their own confirm
     contract and tests.
2. **Cleanup loop in this PR?** Skill-only walk is the “especially cleanup”
   ask and does not need a new mutative CLI.
   - **Recommended:** yes, include the opt-in skill loop.
3. **`status --workspace` alias?** Design doc used a flag. Subcommand is
   cleaner.
   - **Recommended:** subcommand only (no flag).
4. **Split?** If (1) is in-scope too, prefer `/iflow-split` (status/doctor
   vs land vs cleanup) rather than one PR.
   - **Recommended:** keep this PR as status+doctor+dirty+cleanup-token;
     land as a child issue after Accept if you want it tracked.
