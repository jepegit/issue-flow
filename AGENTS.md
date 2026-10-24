# AGENTS.md

Guidance for AI agents working in the **issue-flow** repository.

## What this project is

**issue-flow** is a small Python CLI that scaffolds a lightweight, agent-friendly
issue-tracking workflow into other projects. Running `issue-flow init` writes a
`.issueflows/` tracking tree plus editor skills, rules, and command files where
the selected editor still needs them, so AI agents can pick up GitHub issues,
plan work, and land PRs in a consistent way.

This repo *is* the tool itself — not a project that has been scaffolded by it.

- Package name: `issue-flow` (module `issue_flow`)
- Entry point: `issue-flow = "issue_flow.cli:main"`
- Requires Python 3.12+ (development pin: 3.13 in `.python-version`)
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
uv version --bump <part>           # bump version (used by /iflow-close)
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
  migrate.py        # one-shot migrations `update` applies to older scaffolds
  templates/        # Jinja2 templates for all scaffolded output
    commands/         # thin command wrapper (editors with a commands dir)
    skills/           # Agent Skills: SKILL.md router + mode files per command
    rules/            # always-on rule body (AGENTS.md block) + pointers
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
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md` | Changelog file `/iflow-close` updates |

## Working on issues (this repo's own workflow)

This repo follows the same issue-flow workflow it ships. Issue state lives under
`.issueflows/`:

- `01-current-issues/` — the **focus issue** only (`_original`, `_plan`, `_status`)
- `02-partly-solved-issues/` — parked/in-progress
- `03-solved-issues/` — completed archive
- `00-tools/` — small helper scripts worth keeping
- `04-designs-and-guides/` — durable design docs (not tied to one issue)
- `05-epics/` — staged epic plans (`epic<N>_plan.md`, via `/iflow-issue epic`)

The commands (eleven since #406; the managed block below lists them) follow
`/iflow-pick` → `/iflow-plan` → `/iflow-build` → `/iflow-close` →
`/iflow-cleanup`. `/iflow` dispatches to the next step. Merged commands take a
mode as their first word (`/iflow-run yolo`, `/iflow-issue epic 42`).

Keep status files accurate. Use an explicit checkbox in the status file:
`- [x] Done` when fully resolved, `- [ ] Done` when not.

## Conventions & gotchas

- Do issue work on an **issue branch** (`<N>-<short-slug>`), not the default branch.
- Assume GitHub PRs are **squash-merged**; use `/iflow-cleanup` after merge.
- Before planning/implementing, skim `.issueflows/04-designs-and-guides/` for
  relevant docs and follow them.
- A `graphify-out/` knowledge graph is optional and gitignored here
  (`graphify_gitignored = true`); if present, skim
  `graphify-out/GRAPH_REPORT.md` before grepping.
- Keep the always-on rule and skills within the word budgets in
  `tests/test_command_surface.py`. Put new mode-specific instructions in a
  mode file next to the skill's `SKILL.md`, not in the rule body.
- Only commit when explicitly asked.

## Cursor Cloud specific instructions

- This is a `uv`-managed CLI (Python 3.13, pinned in `.python-version`). `uv` is
  installed at `~/.local/bin` and added to `~/.bashrc`; `uv sync` provisions the
  matching interpreter automatically. Standard commands live in the "Common
  commands" section above (`uv run pytest`, `uv run ruff check src/ tests/`).
- The "application" is the `issue-flow` CLI, exercised end-to-end by scaffolding
  a throwaway project: `git init` an empty dir, then
  `uv run --project /workspace issue-flow init . --skip-dep-check`. Use
  `--skip-dep-check` in headless/cloud runs to avoid the interactive `git`/`gh`
  dependency-check prompt.
- `graphify` is installed as a `uv` tool (`uv tool install graphifyy`), so
  `graphify update .` works without an LLM key (AST-only). `graphify-out/` is
  gitignored in this repo, so a rebuild leaves no diff.

<!-- BEGIN issue-flow (managed: do not edit this block) -->
# Issue-flow

This project tracks GitHub issues with issue-flow. Each `iflow-*` skill holds its own instructions; read a skill only when it is invoked.

## Running Python

Follow the project's documented toolchain (README, `AGENTS.md`, `pyproject.toml`, `environment.yml`, CI). Never call bare `python`: use the project's runner (`uv run …` by default, `conda run -n <env> …` for conda projects, `poetry run …` for poetry). In a uv project, manage dependencies with `uv add` / `uv remove` / `uv sync`, not `pip`.

## Tracking layout

Under `.issueflows/`:

- `00-tools/` — reusable helper scripts; `README.md` is the index. Check it before writing a one-off helper, and add useful tools back.
- `01-current-issues/` — the focus issue only: `issue<N>_original.md`, `issue<N>_plan.md`, `issue<N>_status.md`.
- `02-partly-solved-issues/` — parked work. `03-solved-issues/` — finished work.
- `04-designs-and-guides/` — durable design docs; `this-project.md` is the project brief.
- `05-epics/` — staged epic plans (`epic<N>_plan.md`).

- After each iteration, update `issue<N>_status.md` (done, current state, remaining work) with an explicit checkbox: `- [x] Done` when fully resolved, `- [ ] Done` otherwise. Other steps route files by that checkbox.
- Finished issues move to `03-solved-issues/`, unfinished ones to `02-partly-solved-issues/`.
- Before planning or building, read `04-designs-and-guides/this-project.md` if present and skim `04-designs-and-guides/` for relevant docs. Record non-trivial design decisions there (context, decision, alternatives, issue link).

## Commands

Invoke as `/iflow-<step>` or in chat as `iflow <step> [args]` (also `iflow-<step>` or `/iflow <step>`). A message that **starts with** one of these forms invokes the `iflow-<step>` skill with the trailing text as its arguments; plain `iflow` runs the dispatcher. Mid-sentence mentions are not invocations.

| Command | Purpose |
|---|---|
| `iflow` | Dispatcher: run the next of capture / plan / build / close. |
| `iflow-setup` | Get a project ready (uv, git, GitHub, scaffold). |
| `iflow-pick` | Choose an issue, branch, and capture it. |
| `iflow-plan` | Write the plan and stop for approval. |
| `iflow-build` | Implement the approved plan. |
| `iflow-pause` | Park unfinished work with resume notes. |
| `iflow-close` | Tests, bump, changelog trailers, commit, push, PR. |
| `iflow-cleanup` | After merge: default branch, pull, delete landed branches. |
| `iflow-run` | Hands-off runs under one up-front confirm. |
| `iflow-issue` | Create and shape GitHub issues. |
| `iflow-status` | Read-only overview of every issue. |
The core loop is `pick → plan → build → close → cleanup`. `/iflow` detects the focus issue's state and dispatches to the next of capture / plan / build / close; it never dispatches to any other command. Never skip the plan confirmation in `/iflow-plan` unless a hands-off mode was confirmed.

Issue labels can route `/iflow-pick`: `yolo` → `/iflow-run yolo`, `ops` → no-PR close (ops wins over yolo). A `publish` label makes `/iflow-close` bump the version and release after merge.

## Branch hygiene

- Work on an issue branch `<N>-<short-slug>`, never on the default branch.
- Before continuing a branch, run `git fetch --prune` and check ahead/behind against `origin/<default>`. PRs are **squash**-merged, so a merged branch looks "ahead" and is stale.
- After a PR merges, remind the user to run `/iflow-cleanup`. Do not run it automatically.
- An issue already under `02-partly-solved-issues/` or `03-solved-issues/` has a stale branch. Re-open it only on purpose with `/iflow-pick <N>`.

## Multi-repo workspaces

When the workspace holds several repos with their own `.issueflows/`, resolve the target repo first (`root:` / `repo:` hints, then `issue-flow agent resolve`, then the `issueflow-workspace.toml` default); ask when ambiguous. Pass `--repo <owner/repo>` to every `gh` call. Lifecycle state is per repository.

## Optional skills

- **caveman** — terse response style. **On by default here**: reply in caveman style from the first message of every session. Off with "stop caveman" / "normal mode". Code, commits, PRs, security warnings, and destructive-action confirmations are always normal prose.
- **grill-me** — relentless one-question-at-a-time planning interview. Off until the user asks ("grill me"). Off with "stop grilling".

## Knowledge graph

If `graphify-out/GRAPH_REPORT.md` exists, skim it before grepping. Run `graphify query` / `path` / `explain` only when `graphify-out/graph.json` exists. `/iflow-status graph` rebuilds the graph; nothing runs it automatically.


<!-- END issue-flow (managed) -->
