# Enhance issue-flow CLI for agentic use (issue #88)

## Goal
Promote the most-repeated, deterministic lifecycle mechanics into real `issue-flow` subcommands (at least 5), then teach the skills/commands to use them — while keeping today's manual behavior as a fallback, since the CLI is not guaranteed installed in a scaffolded repo.

## Key findings (from research)
- Today the package only does `init` / `update` / `graphify`. **No Python code reads `.issueflows/`** — all lifecycle mechanics live as agent instructions in templates.
- The CLI is **only available** in a target repo if the user ran `uv tool install issue-flow` or `uv add --dev issue-flow`. So every skill that calls it must fall back to manual steps when it is missing — the same optional-with-fallback pattern `graphify` already uses (`is_available()` via `shutil.which`).
- All 5 chosen commands are deterministic (verified against `iflow.md.j2`, `iflow-status.md.j2`, and the init/start/cleanup sweep rules). The only LLM bits (comment triage, issue ranking, planning) stay agent-side.

## Command surface (hybrid namespace)
- `issue-flow status [--local] [--json]` — top-level, human-facing read-only overview (focus stage, parked, solved, optional GitHub cross-ref). Mirrors `/iflow-status`.
- `issue-flow agent state [--json]` — focus `N` + lifecycle stage + suggested next command. Powers `/iflow` dispatch.
- `issue-flow agent preflight [--json]` — default branch, fetch, clean/dirty, ahead/behind, stale-branch flag.
- `issue-flow agent sweep [--except N] [--dry-run] [--json]` — archive `issue<N>_*` groups `01-` -> `02-`/`03-` by Done checkbox.
- `issue-flow agent capture <N> [--repo owner/repo] [--json]` — `gh issue view` + write `issue<N>_original.md` (body only; prints comments payload for the agent to triage).

All `agent` commands degrade gracefully (missing `gh`/network never hard-fails; emit partial JSON + a note), matching the existing `/iflow-status` "do not fail" rule.

## New Python modules
- `src/issue_flow/tracking.py` — first reader of `.issueflows/`. Functions: `group_issue_files(dir)`, `lifecycle_stage(group)`, `is_done(status_path)` (the `- [x] Done` rule), `resolve_focus(project_root, branch)`, `plan_sweep(...)` / `apply_sweep(...)`. Pure `pathlib` + `re`; uses `Settings.issueflows_subdirs` for folder names.
- `src/issue_flow/gitutils.py` — thin git/gh subprocess helpers following `graphify.py` (`shutil.which` -> build argv -> `subprocess.run(check=False)`): `current_branch`, `default_branch`, `working_tree_status`, `ahead_behind`, `remote_owner_repo` (HTTPS+SSH parse), `gh_issue_view`, `gh_issue_list`. Returns typed results / `None` when a tool is absent; never raises for missing `gh`.
- `src/issue_flow/commands/` (or single `agent.py` + `status.py`) — orchestrators that compose `tracking` + `gitutils` into the report/JSON each command emits.

## CLI wiring (`src/issue_flow/cli.py`)
- Add `@app.command()` `status(...)` with lazy import.
- Create `agent_app = typer.Typer(help=...)`, register `state`/`preflight`/`sweep`/`capture`, then `app.add_typer(agent_app, name="agent")`. Use `raise typer.Exit(code=...)` on failure, mirroring the `graphify` command.

## Templates / skills update (prefer CLI, fall back to manual)
Add a short managed "CLI fast path" note to the high-value surfaces, gated on the CLI being on PATH (mirroring the graphify fallback wording):
- `commands/iflow.md.j2` + `skills/iflow_iflow` — "if `issue-flow` is available, run `issue-flow agent state --json` and dispatch on `next_command`; otherwise do the steps below".
- `commands/iflow-status.md.j2` + `skills/iflow_status` — prefer `issue-flow status`.
- `commands/iflow-init.md.j2` + `skills/iflow_init` — prefer `issue-flow agent capture <N>` and `issue-flow agent sweep --except <N>`.
- `commands/iflow-start.md.j2` + `skills/iflow_start` — prefer `issue-flow agent sweep` and `issue-flow agent preflight`.
- `commands/iflow-plan.md.j2` + `skills/iflow_plan` — prefer `issue-flow agent preflight`.
The manual instructions stay intact below each fast-path note (CLI is optional).

## Docs
- `README.md` — document the new commands; remove `issue-flow status` from "Future plans".
- Bump `src/issue_flow/__init__.py` `__version__` to match `pyproject.toml` (currently stale `0.4.0` vs `0.4.1a3`); real version bump happens at `/iflow-close`.

## Test strategy (`uv run pytest`)
- `tests/test_tracking.py` — group parsing, stage detection, Done rule, sweep dry-run vs apply, `--except`.
- `tests/test_gitutils.py` — owner/repo parse (HTTPS+SSH), ahead/behind parse, default-branch fallback, graceful `None` when tool missing (monkeypatch `subprocess`/`shutil.which`).
- `tests/test_cli.py` — CliRunner smoke for `status` and each `agent` subcommand (monkeypatch git/gh), incl. `--json` shape and exit codes.
- `tests/test_templating.py` — assert the CLI fast-path note + fallback wording renders into the updated surfaces.
- Lint: `uv run ruff check src/ tests/`.

## Scope note
Moderately large but cohesive (two new core modules shared by all 5 commands, plus template touch-ups). Default is one PR.

## Open questions
- None blocking. Defaulting to: one PR; `capture` leaves comment triage to the agent; JSON schemas are new and will be kept stable/minimal.
