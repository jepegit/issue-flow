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

<!-- BEGIN issue-flow (managed: do not edit this block) -->
# Issue-flow best practices


## Running python

This is a python project. It uses a python environment (.venv) managed by uv.

❌ BAD:
```bash
python run_script.py
```

✅ GOOD:
```bash
uv run run_script.py
```

### Package Management with `uv`

**✅ Use `uv` exclusively**

- All Python dependencies **must be installed, synchronized, and locked** using `uv`.
- Never use `pip`, `pip-tools`, or `poetry` directly for dependency management.

**🔁 Managing Dependencies**

```bash
# Add or upgrade dependencies
uv add <package>

# Remove dependencies
uv remove <package>

# Reinstall all dependencies from lock file
uv sync
```

**🔁 Scripts**

```bash
# Run script with proper dependencies
uv run script.py
```


## Issue tracking structure

```bash
issue-flow/
    .issueflows/
        00-tools/
        01-current-issues/
            issueXX_original.md
            issueXX_status.md
        02-partly-solved-issues/
        03-solved-issues/
        04-designs-and-guides/
    pyproject.toml
    readme.md
    ...
```


## Development information


### Working on issues

After each iteration, update the documents in `.issueflows/01-current-issues` (should contain one file labelled `_original` with the original issue description, a `_plan` file with the confirmed approach, and supplementary status files describing what has been done, current status, and remaining work).
Use an explicit status checkbox in the status file:
- `- [x] Done` when fully resolved
- `- [ ] Done` when not fully resolved

### Command lifecycle

If you have not chosen an issue yet, run **`/issue-pick`** — the front door that helps you select the next issue (parked work first, else ranked open GitHub issues), creates the branch, and runs `/issue-init` for you. It is off-path (never auto-dispatched).

If you just want the next right step, run **`/iflow`** — it detects state (by file presence under `.issueflows/01-current-issues/` and the status-file `- [x] Done` marker) and dispatches to `/issue-init`, `/issue-plan`, `/issue-start`, or `/issue-close`. It never auto-dispatches to `/issue-pick`, `/issue-pause`, `/issue-cleanup`, or `/issue-yolo` — those stay explicit.

The full slash-command lifecycle is:

1. **`/issue-init`** — capture the GitHub issue as `issue<N>_original.md`.
2. **`/issue-plan`** — design the approach in `issue<N>_plan.md` and get explicit confirmation before any code changes.
3. **`/issue-start`** — implement the confirmed plan. Asks to run `/issue-plan` first if the plan file is missing.
4. **`/issue-pause`** *(optional)* — park work mid-stream: update status, move the issue group to `02-partly-solved-issues`, optional WIP commit.
5. **`/issue-close`** — tests, optional `uv version --bump`, status update, commit, push, PR. Does not delete branches.
6. **`/issue-cleanup`** — post-merge: switch to default, `git pull --ff-only`, `git fetch --prune`, `git branch -d` on merged local branches under a single consolidated confirm. Never `-D`.

`/issue-yolo` chains `init → plan → start → close` for small, low-risk issues with up-front safeguards (clean tree, passing tests, single consolidated confirm).

> On tools without project slash commands (e.g. Codex CLI), invoke the mirrored Agent Skills instead (for example `issueflow-issue-init` in place of `/issue-init`).

### When finishing an issue

If the issue is fully resolved (no additional subtasks present), move the original, plan, and status markdown files to `.issueflows/03-solved-issues`. Else, move them to `.issueflows/02-partly-solved-issues`.

### Scripts that can help us when working on issues

If you want, you can put small scripts etc. that you have made and think could be useful in the future in our llm tools folder: `.issueflows/00-tools`. Also, feel free to use the tools in our llm tools folder if you find someone that could be useful.


### Designs and guides

Long-lived design docs, design decisions, and project "good practices" live under `.issueflows/04-designs-and-guides/`. Unlike the issue folders, content here is **not** tied to a single issue and is **not** archived when an issue closes — it is the project's durable memory.

- **Before planning or implementing**, skim `.issueflows/04-designs-and-guides/` for existing docs relevant to the current issue and follow them (cite them in the plan when they influence the approach).
- **When a non-trivial design decision is made** during `/issue-plan` or `/issue-start`, add or update a markdown file here. Keep entries terse: context, the decision, alternatives considered, and a link back to the issue.
- **Never overwritten by `issue-flow update`.** The folder is recreated if missing, but existing files are left alone.


### Branch hygiene

- Do issue work on an **issue branch** named like `<N>-<short-slug>`, not on the default branch.
- Before starting or continuing work on an issue branch, run `git fetch --prune` and check where the branch sits relative to `origin/<default>` (ahead/behind). A branch that is "several commits ahead" after a merged PR usually means the PR was squash-merged and the local branch is stale.
- **Assume squash-merges on GitHub.** After a PR merges: run **`/issue-cleanup`** — it switches to the default branch, runs `git pull --ff-only`, `git fetch --prune`, and deletes merged local branches with `git branch -d <branch>` under a single consolidated confirm (never `-D` automatically). `/issue-close` no longer does this step itself.
- If an issue is already archived under `.issueflows/02-partly-solved-issues` or `.issueflows/03-solved-issues`, the matching local branch is stale; don't resume work on it silently — switch back to the default branch and, if the issue really needs re-opening, do it deliberately through `/issue-init` (which will ask for a second confirmation).


### Folder hygiene for `.issueflows/01-current-issues`

- Only the **focus issue** (the one currently being worked on) should live in `.issueflows/01-current-issues`.
- `/issue-init` and `/issue-start` both sweep that folder automatically: every `issue<n>_*` group **other than the focus issue** is moved to `.issueflows/03-solved-issues` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues`. Keep status files accurate so the sweep routes them correctly.


### Knowledge graph (optional, via [graphify](https://graphify.net))

If a `graphify-out/` folder exists in the project root, the project has the optional [graphify](https://graphify.net) integration enabled and a knowledge graph is available alongside the source.

- **Before grepping**, skim `graphify-out/GRAPH_REPORT.md`. It surfaces god-nodes (most-connected concepts), surprising cross-module connections, and suggested questions the graph can answer — often a faster way to locate the files an issue actually touches than full-text search.
- **`/graphify`** (slash command) or **`issue-flow graphify`** (CLI) rebuild the graph. With no extra args this runs `graphify update <project>` — AST-only, **no LLM API key needed**. For richer semantic relationships (cross-file links surfaced by an LLM pass), run `issue-flow graphify extract` after setting `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `MOONSHOT_API_KEY` (or pass `--backend ollama` for a local LLM). Other subcommands: `watch` (live), `cluster-only --no-viz` (re-cluster). Trailing flags pass through verbatim. Your agent's own LLM cannot be reused by subprocesses; graphify needs its own backend.
- `/graphify` is **off-path**: never auto-dispatched by `/iflow`, `/issue-start`, or `/issue-close`. It is the user's call. `/issue-start` may *suggest* skimming `GRAPH_REPORT.md`; `/issue-close` may *suggest* a rebuild after large structural changes — neither runs `graphify` automatically.
- If `graphify-out/` is not present, ignore graph-related guidance entirely. The integration is opt-in (install with `uv tool install graphifyy`, then `issue-flow update` to register the graphify skill).

<!-- END issue-flow (managed) -->
