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
- Requires Python 3.11+ (development pin: 3.13 in `.python-version`)
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
  templates/        # Jinja2 templates for all scaffolded output
    commands/         # /iflow-* slash commands
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
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md` | Changelog file `/iflow-close` updates |

## Working on issues (this repo's own workflow)

This repo follows the same issue-flow workflow it ships. Issue state lives under
`.issueflows/`:

- `01-current-issues/` — the **focus issue** only (`_original`, `_plan`, `_status`)
- `02-partly-solved-issues/` — parked/in-progress
- `03-solved-issues/` — completed archive
- `00-tools/` — small helper scripts worth keeping
- `04-designs-and-guides/` — durable design docs (not tied to one issue)
- `05-epics/` — staged epic plans (`epic<N>_plan.md`, via `/iflow-epic`)

Slash-command lifecycle:

1. `/iflow-pick` — front door: choose the next issue, branch, init (off-path)
2. `/iflow` — smart dispatcher to the right linear step
3. `/iflow-init` → `/iflow-plan` → `/iflow-build` → `/iflow-close` → `/iflow-cleanup`
4. `/iflow-pause` — park work mid-stream
5. `/iflow-yolo` — full chain for small, low-risk issues

Keep status files accurate. Use an explicit checkbox in the status file:
`- [x] Done` when fully resolved, `- [ ] Done` when not.

## Conventions & gotchas

- Do issue work on an **issue branch** (`<N>-<short-slug>`), not the default branch.
- Assume GitHub PRs are **squash-merged**; use `/iflow-cleanup` after merge.
- Before planning/implementing, skim `.issueflows/04-designs-and-guides/` for
  relevant docs and follow them.
- A `graphify-out/` knowledge graph is optional; if present, skim
  `graphify-out/GRAPH_REPORT.md` before grepping. `graphify` is off-path and
  never auto-run.
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
  `graphify update .` works without an LLM key (AST-only). It rewrites the
  tracked `graphify-out/` tree and leaves untracked `graphify-out/cache/`
  files — revert/clean those if you did not intend to commit a graph rebuild.

<!-- BEGIN issue-flow (managed: do not edit this block) -->
# Issue-flow best practices


## Running python

**Respect the project's existing toolchain first.** If this project already
documents how to run Python and manage dependencies — in its `README`,
`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `environment.yml`, `pyproject.toml`,
`Makefile`, CI config, etc. — **follow that**, even where it conflicts with the
defaults below. These rules describe issue-flow's *default* assumptions, not a
mandate to override a project that has already chosen differently.

The one tool-neutral principle: **don't call bare `python ...`** — invoke Python
through the project's environment (its runner, or an activated virtualenv/conda
env) so scripts and tests see the right interpreter and dependencies.

### If the project uses conda

When the project documents a conda environment, run **all** Python commands —
scripts **and `pytest`** — inside the **activated conda environment**. Do **not**
substitute `uv run`.

```bash
# Either activate the environment first…
conda activate <env-name>
python run_script.py
pytest

# …or run one-off commands inside it:
conda run -n <env-name> pytest
```

### If the project uses uv (issue-flow's default)

For projects scaffolded fresh (and this is the default when nothing else is
documented), use `uv`:

```bash
# ❌ BAD: bare interpreter
python run_script.py

# ✅ GOOD: through uv
uv run run_script.py
```

**Package management with `uv`**

- Install, synchronize, and lock dependencies with `uv`; don't reach for `pip`,
  `pip-tools`, or `poetry` in a uv-managed project.

```bash
# Add or upgrade dependencies
uv add <package>

# Remove dependencies
uv remove <package>

# Reinstall all dependencies from the lock file
uv sync

# Run a script with the right environment
uv run script.py
```

### Other toolchains (plain venv / pip / poetry)

If the project uses something else, use whatever it documents (e.g. activate its
`.venv` and use `pip`, or run `poetry run`). Match the project; don't force `uv`.


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
        05-epics/
            epicXX_plan.md
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

### Chat invocation (no slash)

On keyboard layouts where `/` and `@` are awkward to type (for example Norwegian), invoke lifecycle skills in **chat** without special keys.

**Primary form:** `iflow <step>` (space-separated) — e.g. `iflow plan`, `iflow pick`, `iflow close`. Plain `iflow` runs the smart dispatcher.

**Also recognized** (same obligation as slash-menu invocation): hyphen form (`iflow-plan`), slash form (`/iflow-plan`), slash + space (`/iflow plan`).

When the user message is **exactly** one of these forms, or **starts with** it followed by a space and trailing arguments, **read and follow** the matching skill immediately. Forward trailing text verbatim (e.g. `iflow pick fix` → `iflow-pick` with arg `fix`). Do **not** treat incidental mid-sentence mentions as commands — the message must **start with** the invocation.

| Chat / slash form | Skill |
|-------------------|-------|
| `iflow` / `/iflow` | `iflow` (dispatcher) |

| `iflow archive`, `iflow-archive`, `/iflow-archive`, `/iflow archive` | `iflow-archive` |

| `iflow build`, `iflow-build`, `/iflow-build`, `/iflow build` | `iflow-build` |

| `iflow cleanup`, `iflow-cleanup`, `/iflow-cleanup`, `/iflow cleanup` | `iflow-cleanup` |

| `iflow close`, `iflow-close`, `/iflow-close`, `/iflow close` | `iflow-close` |

| `iflow cycle`, `iflow-cycle`, `/iflow-cycle`, `/iflow cycle` | `iflow-cycle` |

| `iflow doctor`, `iflow-doctor`, `/iflow-doctor`, `/iflow doctor` | `iflow-doctor` |

| `iflow epic`, `iflow-epic`, `/iflow-epic`, `/iflow epic` | `iflow-epic` |

| `iflow fix`, `iflow-fix`, `/iflow-fix`, `/iflow fix` | `iflow-fix` |

| `iflow graphify`, `iflow-graphify`, `/iflow-graphify`, `/iflow graphify` | `iflow-graphify` |

| `iflow init`, `iflow-init`, `/iflow-init`, `/iflow init` | `iflow-init` |

| `iflow issue`, `iflow-issue`, `/iflow-issue`, `/iflow issue` | `iflow-issue` |

| `iflow pause`, `iflow-pause`, `/iflow-pause`, `/iflow pause` | `iflow-pause` |

| `iflow pick`, `iflow-pick`, `/iflow-pick`, `/iflow pick` | `iflow-pick` |

| `iflow plan`, `iflow-plan`, `/iflow-plan`, `/iflow plan` | `iflow-plan` |

| `iflow review`, `iflow-review`, `/iflow-review`, `/iflow review` | `iflow-review` |

| `iflow status`, `iflow-status`, `/iflow-status`, `/iflow status` | `iflow-status` |

| `iflow yolo`, `iflow-yolo`, `/iflow-yolo`, `/iflow yolo` | `iflow-yolo` |


Skill `@` attachment is supported on some editors but is not the recommended keyboard-friendly path.

### Command lifecycle

If you have not chosen an issue yet, run **`/iflow-pick`** (or type **`iflow pick`** in chat) — the front door that helps you select the next issue (parked work first, else ranked open GitHub issues), creates the branch, and runs `/iflow-init`. It is off-path (never auto-dispatched).

If you just want the next right step, run **`/iflow`** (or type **`iflow`** in chat) — it detects state (by file presence under `.issueflows/01-current-issues/` and the status-file `- [x] Done` marker) and dispatches to `/iflow-init`, `/iflow-plan`, `/iflow-build`, or `/iflow-close`. It never auto-dispatches to `/iflow-pick`, `/iflow-pause`, `/iflow-cleanup`, or `/iflow-yolo` — those stay explicit.

The full slash-command lifecycle is:

1. **`/iflow-init`** — capture the GitHub issue as `issue<N>_original.md`.
2. **`/iflow-plan`** — design the approach in `issue<N>_plan.md` and get explicit confirmation before any code changes.
3. **`/iflow-build`** — implement the confirmed plan. Asks to run `/iflow-plan` first if the plan file is missing.
4. **`/iflow-pause`** *(optional)* — park work mid-stream: update status, move the issue group to `02-partly-solved-issues`, optional WIP commit.
5. **`/iflow-close`** — tests, optional `uv version --bump`, **changelog/`HISTORY.md` update (in the PR commit)**, status update, commit, push, PR. Does not delete branches. Never offer a HISTORY/CHANGELOG update after the PR is open or merged; use `nohistory` only to skip intentionally.
6. **`/iflow-cleanup`** — post-merge: switch to default, `git pull --ff-only`, `git fetch --prune`, `git branch -d` on merged local branches under a single consolidated confirm. Never `-D`. Trailing `include GitHub` (or similar) adds a remote-branch audit with a second confirm for optional remote deletes / findings issue.

`/iflow-yolo` chains `init → plan → build → close yolo` for small, low-risk issues with up-front safeguards (clean tree, passing tests, single consolidated confirm). Its close step is hands-off: changelog decided without a prompt, PR merged (`gh pr merge --squash`; on pending checks may `gh pr checks --watch` then retry, with `--auto` as last resort), then default-branch switch + pull.


Issue labels can select the flow: when an issue picked via `/iflow-pick` carries the **`yolo`** label, it is routed through `/iflow-yolo` (one combined confirmation). Controlled by `label_flows` (default `true`) and `yolo_label` (default `"yolo"`) under `[issueflow]` in `.issueflows/config.toml`; re-run `issue-flow update` after changing them.



Lifecycle skills include a **`### MODEL & EXECUTION DIRECTIVE`** section that tells agents whether to prioritize **economy** (speed) or **reasoning** (depth) for that step. Toggle with `step_directives` under `[issueflow]`; override per step via `[issueflow.step_profiles]`; optional label hints during `/iflow-pick` via `model_label_flows`, `deep_model_label`, and `fast_model_label`. Re-run `issue-flow update` after changing any of these.


`/iflow-fix` opens an interactive iterative-fixes session: it creates one GitHub issue + long-lived branch, then loops over many small fixes (each gets a short plan and is implemented only on confirmation, recorded as a dated bullet in `issue<N>_status.md`), and ends with `/iflow-close`. It is off-path (never auto-dispatched); while a session is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`.

`/iflow-issue` creates **one well-specified normal GitHub issue** (context / spec / acceptance criteria), then optionally branches and runs `/iflow-init` into the standard lifecycle. It fills the gap between `/iflow-fix` (iterative small-fixes) and `/iflow-epic` (multi-issue staged work). Off-path (never auto-dispatched). For an epic anchor: `/iflow-issue epic <intent>`.

`/iflow-status` prints a **read-only** overview of where every issue stands — the local tracking state under `.issueflows/` (focus / parked / solved) plus open GitHub issues cross-referenced against it. It is off-path (never auto-dispatched) and changes nothing.

`/iflow-doctor` audits `.issueflows/` for **dirty** conditions (ambiguous multi-focus, leftovers in `01-current-issues/`, duplicates across folders, and similar) and can apply **safe repairs** on confirmation (`issue-flow doctor` / `agent audit` + `repair`). It is off-path and never auto-dispatched.

`/iflow-review` reviews open GitHub issues and applies labels (extendable kinds; v1: **yolo** → configured `yolo_label`). Off-path; consolidated confirm before any label create/apply; never auto-dispatched. CLI helpers: `issue-flow agent label-candidates` / `label-apply`.

`/iflow-epic <N>` plans a change **too large for one issue** as a staged epic: it drafts `.issueflows/05-epics/epic<N>_plan.md` (anchored to GitHub issue `<N>`), dividing the work into sequential stages of manageable issue specs with explicit dependencies and a per-issue yolo-fitness judgment. Drafting writes nothing on GitHub; **`/iflow-epic <N> publish [stage <k>]`** creates a confirmed stage's issues behind one consolidated confirm (yolo labels per the recorded judgment, task list maintained on the anchor issue, `Published: #<M>` recorded back into the plan so re-runs are idempotent). Off-path (never auto-dispatched); epics decompose into the normal single-issue lifecycle, never around it.

`/iflow-cycle <queue-spec>` processes **many issues hands-off in a row** under a single up-front confirmation — the batch equivalent of `/iflow-yolo`. It resolves a queue via `issue-flow agent queue` (explicit numbers, `label:<L>`, or `epic <N> [stage <k>]`), then runs each issue through the full yolo chain (PR auto-merged), interrupting you only when input is **strictly necessary** (unfixable failure, refused merge / non-fast-forward pull, ambiguous or not-actually-small spec, or anything outside the confirmed queue). It stops the whole cycle on the first such condition, leaving the repo clean on the default branch. **All yolo-labelled issues:** `/iflow-cycle yolo` (alias for `label:yolo`). Off-path (never auto-dispatched); never weakens a yolo safeguard to keep moving.

`/iflow-archive` condenses old solved issue groups under `.issueflows/03-solved-issues/` into a single dated `YYYY-MM-DD_archived_issues.md` summary file (recording the pre-archive git ref for recovery via `git show <ref>:<path>`), then deletes the original `issue<N>_*` files. It is off-path and destructive: nothing is deleted before one consolidated confirmation.

> On tools without project slash commands (e.g. Codex CLI), invoke the mirrored Agent Skills instead (for example `iflow-init` in place of `/iflow-init`).

### When finishing an issue

If the issue is fully resolved (no additional subtasks present), move the original, plan, and status markdown files to `.issueflows/03-solved-issues`. Else, move them to `.issueflows/02-partly-solved-issues`.

### Scripts that can help us when working on issues

`.issueflows/00-tools/` is the project's durable toolbox of reusable helper scripts, with a `README.md` index describing each one.

- **Check it first.** Before writing a new one-off helper for an issue, skim the `00-tools/README.md` index and the folder — a suitable tool may already exist.
- **Contribute back.** If you build something during an issue that could help on a future one, save it into `.issueflows/00-tools/` and add a one-line entry to the index (name, what it does, when to use it) so the next agent knows whether to reach for it.



### Optional response styles

A **caveman** Agent Skill is installed under `.cursor/skills/caveman/` and
is **on by default for this project**: reply in the terse, "token-greedy" caveman
style — keep all technical substance, drop filler, articles, and pleasantries —
from the first message of every session, re-arming each new session. Turn it off
for the rest of a session with **"stop caveman"** or **"normal mode"**. Code,
commits, PRs, security warnings, and destructive-action confirmations are always
written in normal prose, never caveman. (This default comes from
`caveman_default = true` under `[issueflow]` in `.issueflows/config.toml`;
set it to `false` and re-run `issue-flow update` to make caveman opt-in per
session instead.)




### Planning aids

A **grill-me** Agent Skill is installed under `.cursor/skills/grill-me/`.
It runs a relentless planning interview that stress-tests a plan or design —
one question at a time, each with a recommended answer — until every branch of
the decision tree is resolved. It is **off by default** and only kicks in when
you ask for it (e.g. "grill me", "poke holes in this"). Turn it off with **"stop
grilling"** or **"normal mode"**. (To make grilling on by default during planning
for this project, set `grill_me_default = true` under `[issueflow]` in
`.issueflows/config.toml` and re-run `issue-flow update`.)



### Designs and guides

Long-lived design docs, design decisions, and project "good practices" live under `.issueflows/04-designs-and-guides/`. Unlike the issue folders, content here is **not** tied to a single issue and is **not** archived when an issue closes — it is the project's durable memory.

- **Project brief:** if `.issueflows/04-designs-and-guides/this-project.md` exists, read it early for project-specific context (what the repo is, stack/runtime, how to run/test, conventions, entry points, and known limitations).
- **Before planning or implementing**, skim `.issueflows/04-designs-and-guides/` for existing docs relevant to the current issue and follow them (cite them in the plan when they influence the approach).
- **When a non-trivial design decision is made** during `/iflow-plan` or `/iflow-build`, add or update a markdown file here. Keep entries terse: context, the decision, alternatives considered, and a link back to the issue.
- **Never overwritten by `issue-flow update`.** The folder is recreated if missing, but existing files are left alone.


### Multi-root workspaces

When an editor workspace contains **multiple sibling repositories**, each with its own `.issueflows/` scaffold:

- **Resolve the target repo first** — explicit `root:` / `repo:` hints, then `issue-flow agent resolve`, then branch/single-scaffold heuristics, then the **workspace default** from `issueflow-workspace.toml` at the workspace root (create it with `issue-flow workspace init`); **ask** when still ambiguous. Never let `git` or `gh` infer the repo from cwd alone.
- **Scoped rules** — this repo's `issueflow-rules` apply under this project root only (path globs). Put **toolchain-specific** run/test commands in `.issueflows/04-designs-and-guides/this-project.md`, not in shared boilerplate that every repo merges.
- **Per-repo lifecycle** — `/iflow-cleanup`, branch hygiene, and focus issue folders are **per repository**; repeat commands in each repo when needed.
- **Design doc** — see `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` when present (issue #67).


### Branch hygiene

- Do issue work on an **issue branch** named like `<N>-<short-slug>`, not on the default branch.
- Before starting or continuing work on an issue branch, run `git fetch --prune` and check where the branch sits relative to `origin/<default>` (ahead/behind). A branch that is "several commits ahead" after a merged PR usually means the PR was merged (this project uses **`squash`**) and the local branch is stale.
- **Assume `squash` merges on GitHub.** After a PR merges: run **`/iflow-cleanup`** — it switches to the default branch, runs `git pull --ff-only`, `git fetch --prune`, and deletes merged local branches with `git branch -d <branch>` under a single consolidated confirm (never `-D` automatically). `/iflow-close` no longer does this step itself.

- If an issue is already archived under `.issueflows/02-partly-solved-issues` or `.issueflows/03-solved-issues`, the matching local branch is stale; don't resume work on it silently — switch back to the default branch and, if the issue really needs re-opening, do it deliberately through `/iflow-init` (which will ask for a second confirmation).


### Folder hygiene for `.issueflows/01-current-issues`

- Only the **focus issue** (the one currently being worked on) should live in `.issueflows/01-current-issues`.
- `/iflow-init` and `/iflow-build` both sweep that folder automatically: every `issue<n>_*` group **other than the focus issue** is moved to `.issueflows/03-solved-issues` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues`. Keep status files accurate so the sweep routes them correctly.


### Knowledge graph (optional, via [graphify](https://iflow-graphify.net))

If a `graphify-out/` folder exists in the project root, the project has the optional [graphify](https://iflow-graphify.net) integration enabled and a knowledge graph is available alongside the source.

- **Before grepping**, skim `graphify-out/GRAPH_REPORT.md`. It surfaces god-nodes (most-connected concepts), surprising cross-module connections, and suggested questions the graph can answer — often a faster way to locate the files an issue actually touches than full-text search.
- **`/iflow-graphify`** (slash command) or **`issue-flow graphify`** (CLI) rebuild the graph. With no extra args this runs `graphify update <project>` — AST-only, **no LLM API key needed**. For richer semantic relationships (cross-file links surfaced by an LLM pass), run `issue-flow graphify extract` after setting `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `MOONSHOT_API_KEY` (or pass `--backend ollama` for a local LLM). Other subcommands: `watch` (live), `cluster-only --no-viz` (re-cluster). Trailing flags pass through verbatim. Your agent's own LLM cannot be reused by subprocesses; graphify needs its own backend.
- `/iflow-graphify` is **off-path**: never auto-dispatched by `/iflow`, `/iflow-build`, or `/iflow-close`. It is the user's call. `/iflow-build` may *suggest* skimming `GRAPH_REPORT.md`; `/iflow-close` may *suggest* a rebuild after large structural changes — neither runs `graphify` automatically.
- If `graphify-out/` is not present, ignore graph-related guidance entirely. The integration is opt-in (install with `uv tool install graphifyy`, then `issue-flow update` to register the graphify skill).

<!-- END issue-flow (managed) -->
