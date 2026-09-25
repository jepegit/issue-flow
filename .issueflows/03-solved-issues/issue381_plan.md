# Plan: #381 git processing all repos in workspace

## Goal

Give agents and humans one CLI to run **git hygiene across every workspace
member** — starting with a `git status`-shaped snapshot (branch, dirty
paths, ahead/behind). Document it; do not invent a parallel issue-tracker
status.

## Constraints

- Members come from `issueflow-workspace.toml` via existing
  `_prepare_workspace_members` (walk-up, locked skip, continue-on-fail).
  Never guess sibling folders that are not members.
- Read-only for `status`. `fetch` is `--prune` only. **No** pull, rebase,
  merge, push, stash, or reset in this issue (those need per-repo
  `default-sync` / confirms; `workspace land` stays the #318 follow-up).
- Do **not** overload `workspace status` (that is issue-flow lifecycle
  status) or `workspace dirty` (post-update dirt class). New git verbs
  live under `workspace git`.
- `--editor` / project skills stay per-repo. No new lifecycle slash
  command that auto-dispatches from `/iflow`.
- Honour `git -C <member>` and never operate on the workspace parent as
  if it were a repo.

### Prior art

- `issue-flow workspace status|doctor|dirty` + `_prepare_workspace_members`
  (`src/issue_flow/agent.py`, `cli.py`, `tests/test_workspace_actions.py`)
  — #318 fan-out loop. **Reuse** the loop; new verbs only.
- `issue-flow agent preflight` — single-repo branch / dirty / ahead-behind
  (always `fetch --prune`). **Reuse payload fields**, do **not** fan-out
  preflight as-is (N fetches on every status).
- `gitutils.dirty_paths` / `ahead_behind` / `current_branch` /
  `default_branch` / `fetch_prune`.
- `/iflow-status workspace` / `/iflow-cleanup workspace` — issue and
  branch-hygiene fan-out, not raw git. **Coexist**; mention the new CLI
  in docs/skills.
- Toolbox: no git fan-out script. No new `00-tools/` helper.
- Graph: `graphify-out/` absent in this worktree; skipped.

## Approach

Add Typer group `issue-flow workspace git`:

| Command | Behaviour |
| --- | --- |
| `issue-flow workspace git status` (also default if no verb) | Per member: `name`, `path`, `branch`, `default_branch`, `clean`, `dirty_paths`, `issueflows_only`, `ahead`, `behind`. Text: one line each (`name  branch  N ahead / M behind  clean\|dirty`). `--json` aggregate like other workspace cmds. **No fetch.** |
| `issue-flow workspace git fetch` | `git fetch --prune` per member. Report ok/fail. `--json` same shape. |

Implementation:

1. `run_workspace_git_status` / `run_workspace_git_fetch` next to
   `run_workspace_dirty`, sharing `_prepare_workspace_members`.
2. Status builds the snapshot from `gitutils` without calling
   `run_preflight` (avoids implicit fetch + stale-issue notes).
3. Nested `typer.Typer` under `workspace_app` (`name="git"`).
4. Docs: `docs/cli.md`, `docs/how-to/workspaces.md`,
   `multi-repo-workspaces.md` (Phase 4 addendum: git verbs).
5. **Skill (thin, off-path):** new `iflow-workspace-git` (command +
   skill template). Invoke `iflow git` / `/iflow-workspace-git`. Read-only
   recipe: resolve workspace → `workspace git status [--json]`; optional
   trailing `fetch` runs fetch then status. Never auto-dispatched. One
   paragraph in `iflow-status` pointing here so agents do not confuse
   `workspace status` with git.
6. Design note in `multi-repo-workspaces.md`: v1 verbs; pull/push out of
   scope.

Suggested later verbs (document only, do not build): `pull` (ff-only +
`default-sync` abort), `workspace land` (#318).

## Files to touch

- `src/issue_flow/cli.py` — `workspace git` group.
- `src/issue_flow/agent.py` — `run_workspace_git_status` /
  `run_workspace_git_fetch`.
- `tests/test_workspace_actions.py` — status + fetch fan-out (locked skip,
  continue-on-fail, `--json`).
- `src/issue_flow/templates/commands/iflow-workspace-git.md.j2`
- `src/issue_flow/templates/skills/iflow_workspace_git/SKILL.md.j2`
- templating / command+skill registries (same pattern as other off-path
  commands).
- `src/issue_flow/templates/skills/iflow_status/SKILL.md.j2` — pointer.
- `docs/cli.md`, `docs/how-to/workspaces.md`
- `.issueflows/04-designs-and-guides/multi-repo-workspaces.md`
- `.issueflows/04-designs-and-guides/test-registry.md`

## Test strategy

`uv run pytest` (essential: new cases in `test_workspace_actions.py`).

- Two-member workspace: one dirty, one clean + ahead/behind mocked or
  real git.
- Locked member skipped.
- Fetch: `git fetch` invoked per unlocked member; one failure does not
  abort the rest; exit 1 if any fail.
- `workspace git --help` lists `status` / `fetch`.
- Scaffold/render: new command+skill names appear for standard mode.

`uv run ruff check src/ tests/` on touched files.

## Open questions

None blocking if the defaults below are Accept-ok:

1. **Name:** `workspace git status|fetch` (recommended) vs enrich
   `workspace dirty` vs `workspace preflight`.
2. **Skill:** thin off-path `iflow-workspace-git` (recommended) vs docs
   only.
3. **Fetch on status?** No (recommended). Separate `fetch` verb.
