# Plan — issue #158: workspace-wide `issue-flow update`

## Goal

Add `issue-flow workspace update` so a multi-repo workspace with `issueflow-workspace.toml` can refresh every scaffolded member repo in one shot — no manual `cd` + `issue-flow update` per repo.

## Constraints

- Reuse existing workspace discovery (`discover_workspace`, `Workspace.member_roots`) and per-repo `run_update` — no duplicate scaffold logic.
- Each member keeps its own persisted `mode` / `skill_level` from its `.issueflows/config.toml` (same as today’s top-level `update`).
- Only members with a scaffold (`.issueflows/`) are touched — same filter as `workspace init` / `load_workspace`.
- Non-destructive to issue markdown under `.issueflows/` (inherited from `run_update`).
- Follow existing CLI patterns: Typer subcommand under `workspace`, `--json`, pass-through `--skip-dep-check` and `--editor`.

### Prior art

- `discover_workspace()` / `Workspace.member_roots()` — [`src/issue_flow/project.py`](src/issue_flow/project.py) (issue #126).
- `run_workspace_init()` — [`src/issue_flow/agent.py`](src/issue_flow/agent.py) (batch workspace command pattern, JSON payload, error messages).
- `run_update()` — [`src/issue_flow/init.py`](src/issue_flow/init.py) (per-repo refresh; raises `typer.Exit` on failure).
- `issue-flow workspace init` — [`src/issue_flow/cli.py`](src/issue_flow/cli.py) (`workspace_app` typer group).
- Design context — [`.issueflows/04-designs-and-guides/multi-repo-workspaces.md`](.issueflows/04-designs-and-guides/multi-repo-workspaces.md) (currently says “re-run `issue-flow update` in each repo”; Phase 4 mentions `status --workspace` but not batch update).
- Tests — `_seed_workspace()` / `test_workspace_init_*` in [`tests/test_cli.py`](tests/test_cli.py); workspace discovery in [`tests/test_project.py`](tests/test_project.py).
- Graph communities touching workspace: Community hubs around `discover_workspace`, `load_workspace`, `run_workspace_init` (GRAPH_REPORT § workspace registry).
- Toolbox: no existing helper for batch update (`00-tools/` checked).

## Approach

### CLI surface

```
issue-flow workspace update [WORKSPACE_DIR] [--skip-dep-check] [--editor …] [--json]
```

- `WORKSPACE_DIR` defaults to `.` (walk parents for `issueflow-workspace.toml`, same as `discover_workspace`).
- On missing / unparseable registry → exit 1 with actionable message (mirror `workspace init` tone).
- On zero scaffolded members → exit 1 (“run `issue-flow init` in member repos first”).
- Iterate `workspace.member_roots()` in stable order (member name sort, already how `load_workspace` builds the list).
- For each member: call `run_update(member_root, skip_dep_check=…, editors=…)` inside `try/except typer.Exit` so one failure does not abort the rest.
- Run dependency gate once before the loop when `skip_dep_check` is false (call existing `_dependency_gate` or first `run_update` with check, subsequent with `skip_dep_check=True`) to avoid N identical prompts.
- Text mode: print a short header (`workspace root`, member count), then per-member section (reuse `run_update`’s existing Rich output), then a one-line summary (`N/M succeeded`).
- `--json`: emit `{ workspace_root, members: [{ path, name, ok, error? }], ok_count, fail_count }`; exit 0 only when all succeed.

### Implementation sketch

1. Add `run_workspace_update(workspace_dir, console, skip_dep_check, editors, as_json) -> int` in `agent.py` next to `run_workspace_init`.
2. Wire `@workspace_app.command("update")` in `cli.py` with the same flags as top-level `update` where applicable.
3. Update `multi-repo-workspaces.md` Phase 1 bullet (“run `issue-flow update` in each repo”) to mention `issue-flow workspace update` as the batch path; keep per-repo `update` valid.
4. No template changes required (no new scaffolded surfaces).

### Yolo fitness

**Good yolo candidate** — single focused feature, ~1 new function + CLI wiring + tests, reuses proven paths, low blast radius, no cross-repo git/gh side effects.

## Files to touch

| Path | Change |
|------|--------|
| [`src/issue_flow/agent.py`](src/issue_flow/agent.py) | `run_workspace_update()` — discover, loop members, aggregate results |
| [`src/issue_flow/cli.py`](src/issue_flow/cli.py) | `workspace update` subcommand |
| [`tests/test_cli.py`](tests/test_cli.py) | Happy path (2 members updated), no registry, partial failure, `--json` |
| [`.issueflows/04-designs-and-guides/multi-repo-workspaces.md`](.issueflows/04-designs-and-guides/multi-repo-workspaces.md) | Document batch update command |

## Test strategy

```bash
uv run pytest tests/test_cli.py -k workspace
uv run ruff check src/ tests/
```

New tests (tmp_path fixtures like existing workspace tests):

1. Two scaffolded members → both get manifest refresh (assert a known template marker in a rendered file, or spy/mock `run_update` if lighter).
2. No `issueflow-workspace.toml` → exit 1.
3. One member with invalid/missing mode config → other member still updates; exit 1; JSON lists per-member `ok`/`error`.

## Open questions

1. **Partial failure exit code** — plan assumes exit 1 when any member fails (standard batch). OK?
2. **Verbose output** — plan keeps full per-repo `run_update` Rich output (simplest). Prefer a `--quiet` flag in v1 or defer?
