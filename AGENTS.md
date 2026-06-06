# AGENTS.md

Guidance for AI agents working in the **issue-flow** repository.

## What this project is

**issue-flow** is a small Python CLI that scaffolds a lightweight, agent-friendly
issue-tracking workflow into other projects. Running `issue-flow init` writes a
`.issueflows/` tracking tree plus Cursor slash commands, skills, and rules so that
AI agents can pick up GitHub issues, plan work, and land PRs in a consistent way.

This repo *is* the tool itself — not a project that has been scaffolded by it.

- Package name: `issue-flow` (module `issue_flow`)
- Entry point: `issue-flow = "issue_flow.cli:main"`
- Requires Python 3.13+
- Source of truth for scaffolded files: Jinja2 templates under
  `src/issue_flow/templates/`

## Environment & tooling

This project uses a `uv`-managed virtual environment (`.venv`). **Use `uv`
exclusively** for dependency management and running code — never `pip`,
`pip-tools`, or `poetry`.

```bash
uv sync                 # install/refresh all deps from the lock file
uv add <package>        # add or upgrade a dependency
uv remove <package>     # remove a dependency
uv run <script.py>      # run a script with the right environment
```

❌ `python run_script.py`  →  ✅ `uv run run_script.py`

## Common commands

```bash
uv run pytest                      # run the test suite
uv run ruff check src/ tests/      # lint
uv version --bump <part>           # bump version (used by /issue-close)
```

## Project layout

```text
src/issue_flow/
  cli.py            # Typer CLI: init / update / graphify
  init.py           # scaffolding logic (writes .issueflows/ + .cursor/)
  config.py         # env-driven config (ISSUEFLOW_* vars, .env)
  dependencies.py   # external-CLI checks (git, gh)
  templating.py     # Jinja2 rendering helpers
  graphify.py       # optional graphify integration
  templates/        # Jinja2 templates for all scaffolded output
    commands/         # /issue-* slash commands
    skills/           # Agent Skills
    rules/            # always-on Cursor rule
tests/              # pytest suite
```

> **Important:** the files generated into a target project (slash commands,
> skills, rules) come from `src/issue_flow/templates/`. When changing scaffold
> behavior, edit the **templates**, not any already-rendered copy.

## Configuration

issue-flow reads a `.env` from the project root (python-dotenv):

| Variable | Default | Description |
|---|---|---|
| `ISSUEFLOW_DIR` | `.issueflows` | Issue-tracking directory name |
| `ISSUEFLOW_AGENT_DIR` | `.cursor` | Agent/IDE config directory |
| `ISSUEFLOW_DOCS_DIR` | `docs` | Where the workflow doc is written |
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md` | Changelog file `/issue-close` updates |

## Working on issues (this repo's own workflow)

This repo follows the same issue-flow workflow it ships. Issue state lives under
`.issueflows/`:

- `01-current-issues/` — the **focus issue** only (`_original`, `_plan`, `_status`)
- `02-partly-solved-issues/` — parked/in-progress
- `03-solved-issues/` — completed archive
- `00-tools/` — small helper scripts worth keeping
- `04-designs-and-guides/` — durable design docs (not tied to one issue)

Slash-command lifecycle:

1. `/issue-pick` — front door: choose the next issue, branch, init (off-path)
2. `/iflow` — smart dispatcher to the right linear step
3. `/issue-init` → `/issue-plan` → `/issue-start` → `/issue-close` → `/issue-cleanup`
4. `/issue-pause` — park work mid-stream
5. `/issue-yolo` — full chain for small, low-risk issues

Keep status files accurate. Use an explicit checkbox in the status file:
`- [x] Done` when fully resolved, `- [ ] Done` when not.

## Conventions & gotchas

- Do issue work on an **issue branch** (`<N>-<short-slug>`), not the default branch.
- Assume GitHub PRs are **squash-merged**; use `/issue-cleanup` after merge.
- Before planning/implementing, skim `.issueflows/04-designs-and-guides/` for
  relevant docs and follow them.
- A `graphify-out/` knowledge graph is optional; if present, skim
  `graphify-out/GRAPH_REPORT.md` before grepping. `graphify` is off-path and
  never auto-run.
- Only commit when explicitly asked.
