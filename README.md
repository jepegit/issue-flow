# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project so that AI coding agents can pick up GitHub issues, plan work, and land PRs in a consistent way. It supports **Cursor, Claude Code, opencode, and Codex** via `--editor` (see [Editor support](#editor-support)); the examples below use the default, Cursor.

## What it does

Running `issue-flow init` in your project root creates:

```text
your-project/
  .issueflows/
    00-tools/                # Helper scripts for agents
    01-current-issues/       # Active issue markdown files
    02-partly-solved-issues/ # Parked / in-progress issues
    03-solved-issues/        # Completed issues archive
    04-designs-and-guides/   # Durable project context and decisions
      this-project.md        # Hand-editable project brief (created if missing)
  .cursor/
    skills/                  # Agent Skills (explicit / @ invoke; shown in slash menu)
      iflow-pick/SKILL.md
      iflow/SKILL.md
      iflow-init/SKILL.md
      iflow-plan/SKILL.md
      iflow-start/SKILL.md
      iflow-pause/SKILL.md
      iflow-close/SKILL.md
      iflow-cleanup/SKILL.md
      iflow-yolo/SKILL.md
      iflow-fix/SKILL.md
      iflow-status/SKILL.md
      iflow-version-bump/SKILL.md
      iflow-history-update/SKILL.md
      iflow-graphify/SKILL.md
    rules/
      issueflow-rules.mdc    # Always-on Cursor rule for the workflow
  AGENTS.md                  # Workflow rules (managed block; shared by all editors)
  docs/
    issue-workflow.md        # Human-readable overview of the workflow
```

The exact `agent_dir` and the per-editor rules file depend on which editor(s) you scaffold for — see [Editor support](#editor-support). `AGENTS.md` (written as a non-destructive managed block), `.issueflows/04-designs-and-guides/this-project.md` (a hand-editable project brief created only when missing), and `docs/issue-workflow.md` are shared by every editor.

The Cursor Agent Skills give agents a repeatable flow and appear in the slash menu. The linear path is:

1. `/iflow-init 42` — pulls GitHub issue #42 into `.issueflows/01-current-issues/` and archives older issues.
2. `/iflow-plan` — drafts `issue<N>_plan.md` (Goal / Constraints / Approach / Files to touch / Test strategy / Open questions) and stops for your confirmation.
3. `/iflow-start` — reads the confirmed plan and implements it. If no plan file exists, it offers to run `/iflow-plan` first, proceed without a plan, or abort.
4. `/iflow-close` — runs tests, optionally bumps version with `uv version --bump`, appends a `HISTORY.md` entry (or promotes `[Unreleased]` to a new release section on a bump), updates status files, commits, pushes, and opens a PR.
5. `/iflow-cleanup` — after the PR merges, switches to the default branch, fast-forwards, prunes, and deletes the merged local branch.

Plus a few off-path commands:

- `/iflow-pick` — **front door**: when you haven't chosen an issue yet, it helps pick one (parked work in `02-partly-solved-issues/` first, else open GitHub issues ranked by milestone, labels, and similarity to recently solved work), creates the `<N>-slug` branch, and runs `/iflow-init`. Pass `fix` to create a new general-fixes issue. Off-path; never auto-dispatched.
- `/iflow` — **quick start**: inspects the current issue's state and dispatches to the right linear step automatically. A branch-derived number (`42-fix-login` → `N=42`) is authoritative, so `/iflow` works from a fresh branch too.
- `/iflow-pause` — park the current issue in `02-partly-solved-issues/` with a **Remaining work** note; optional WIP commit + switch back to the default branch.
- `/iflow-yolo` — all-in-one chain (`init → plan → start → close`) for small, low-risk issues, with up-front safeguards (refuses on the default branch, refuses with dirty unrelated changes, requires passing tests, single consolidated confirm).
- `/iflow-fix` — interactive iterative-fixes session: creates one GitHub issue + long-lived branch, then loops over many small fixes (each gets a short plan, implemented only on confirmation and recorded in `issue<N>_status.md`), ending with `/iflow-close`. Coexists with `/iflow-pick fix` (the one-shot setup). Off-path; never auto-dispatched.
- `/iflow-status` — **read-only** overview of where every issue stands: the local tracking state (focus / parked / solved) plus open GitHub issues cross-referenced against it. Pass `local` to skip the GitHub query. Changes nothing; off-path; never auto-dispatched.

The **Agent Skills** under `.cursor/skills/` carry the workflows for on-demand use with `/iflow-pick`, `/iflow`, `/iflow-init`, `/iflow-plan`, `/iflow-start`, `/iflow-pause`, `/iflow-close`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-fix`, `/iflow-status`, `@iflow-version-bump` when you need only the bump steps, or `@iflow-history-update` when you need only the changelog update (see [Cursor Agent Skills](https://cursor.com/help/customization/skills)).

## Prerequisites

issue-flow itself is a small Python CLI, but the **scaffolded commands and skills
it writes into your project shell out to a few external tools**. If they are
missing, the workflows will fail at runtime — so `issue-flow init` now
checks for them up front and prints install hints before it does anything.

Required:

- **[Git](https://git-scm.com/downloads)** — used by every slash command for
branch, fetch, status, commit, and push operations. Almost certainly already
installed if you're here, but the check covers it for completeness.
- **[GitHub CLI (`gh`)](https://cli.github.com/)** — used by `/iflow-init` to
fetch issues, by `/iflow-close` to open PRs, and by `/iflow-cleanup` to check
PR merge status. After installing, run `gh auth login` once to authenticate.

Recommended:

- **[uv](https://docs.astral.sh/uv/)** — how issue-flow itself is meant to be
installed, and how this repo manages its own Python environment.

Quick install pointers for `gh`:


| Platform              | Command                                                                                        |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| macOS (Homebrew)      | `brew install gh`                                                                              |
| Windows (winget)      | `winget install --id GitHub.cli -e`                                                            |
| Linux (Debian/Ubuntu) | `sudo apt install gh` (or see [cli.github.com](https://cli.github.com/) for the official repo) |


If a dependency is missing, `issue-flow init` prints the installation hints
and asks whether to continue anyway. You can bypass the prompt in automation
with `issue-flow init --skip-dep-check` (the same flag is available on
`issue-flow update`), and the prompt is also auto-skipped when stdin is not
a TTY (e.g. CI pipelines).

### Optional: graphify integration

issue-flow has a lightweight integration with [graphify](https://iflow-graphify.net)
(PyPI: `graphifyy`, CLI: `graphify`) — a tool that turns the project into a
queryable knowledge graph that AI assistants can read instead of grepping
through files. The integration is **opt-in by installing `graphifyy` as its
own tool** (the same way you installed issue-flow): there is no enable flag and
no extras to remember — detection is purely PATH-based. (You *can* keep an LLM
API key in `.env` for the optional `extract` pass; see below.)

What `issue-flow` does when `graphify` is on PATH:

- `issue-flow init` and `issue-flow update` run `graphify cursor install` so
the graphify Cursor skill is registered alongside the issue-flow scaffold.
If graphify is not installed, both commands just print install hints and
continue — they never block.
- A new `/iflow-graphify` entry point (skill on Cursor/Codex, command + skill
for command-emitting editors) wraps
`issue-flow graphify`. With no extra args it runs `graphify update <project>`
— AST-only, **no LLM API key required**, so the no-arg case "just works".
For richer semantic relationships add `extract` (`issue-flow graphify extract`)
and configure a backend (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, `MOONSHOT_API_KEY`, or `--backend ollama` for a local
LLM). You can set that key in the project `.env` — `issue-flow graphify`
loads `.env` from the project root before invoking graphify — or export it in
your shell environment. Cursor's own LLM is not available to subprocesses, so
graphify needs its own backend. Other subcommands (`watch`, `cluster-only`, …)
pass through too; trailing flags forward verbatim.
- The scaffolded rules and `/iflow-start` mention `graphify-out/GRAPH_REPORT.md`
as a recommended pre-read when the file exists. `/iflow-graphify` is **off-path** —
`/iflow` never auto-dispatches to it.

To enable, install graphify as its own standalone tool:

```bash
uv tool install graphifyy   # recommended
# or
pipx install graphifyy
# or
pip install graphifyy
```

> **Why not an `issue-flow[graphify]` extra (or `uv tool install issue-flow --with graphifyy`)?**
> `uv tool install` only puts the **host package's** entry-point scripts on
> PATH. An extra (or `--with graphifyy`) pulls graphifyy into issue-flow's
> venv but leaves the `graphify` CLI invisible to the shell, so `/iflow-graphify`
> and `graphify cursor install` would still fail. Installing graphify as
> its own tool puts a real `graphify` shim on PATH and matches how we
> treat `git` / `gh`.

> **Just installed graphifyy and `issue-flow init` says it's still missing?**
> uv prints `~/.local/bin is not on your PATH` after the first
> `uv tool install`. Run `uv tool update-shell` (refreshes shell rc files),
> then **restart your shell and Cursor** so the new PATH takes effect.
> issue-flow's missing-CLI hint also detects this case and tells you the
> exact directory to add.

After installing, run `issue-flow update` once so the graphify Cursor skill
gets registered.

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv tool install issue-flow
```

Or add it as a dev dependency to your project:

```bash
uv add --dev issue-flow
```

## Quick start

```bash
cd your-project
issue-flow init
```

That's it. Open the project in Cursor and start with `/iflow` (or step through `/iflow-init`, `/iflow-plan`, `/iflow-start`, `/iflow-close`, `/iflow-cleanup` explicitly).

## Usage

```
issue-flow init [PROJECT_DIR] [--force] [--skip-dep-check] [--editor EDITOR] [--mode MODE] [--skill-level LEVEL]
issue-flow update [PROJECT_DIR] [--skip-dep-check] [--editor EDITOR]
issue-flow graphify [-C PROJECT_DIR] [...graphify subcommand + args]
issue-flow status [PROJECT_DIR] [--local] [--json]
issue-flow agent state [PROJECT_DIR] [--json]
issue-flow agent preflight [PROJECT_DIR] [--json]
issue-flow agent sweep [PROJECT_DIR] [--except N] [--dry-run] [--json]
issue-flow agent capture N [-C PROJECT_DIR] [--repo OWNER/REPO] [--force] [--json]
```

### `issue-flow init`


| Argument / Option  | Description                                                                                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROJECT_DIR`      | Project root directory. Defaults to `.` (current directory).                                                                                                               |
| `--force`, `-f`    | Overwrite generated commands, rules, and workflow doc instead of skipping them.                                                                                            |
| `--skip-dep-check` | Skip the external-CLI dependency check (`git`, `gh`) and the confirmation prompt that follows if anything is missing. Useful in automation.                                |
| `--editor`, `-e`   | AI coding tool(s) to scaffold for: `cursor` (default), `claude`, `opencode`, `codex`, or `all`. Repeatable (`-e cursor -e claude`). See [Editor support](#editor-support). |
| `--mode`, `-m`     | Scaffolding mode — which workflow surfaces to install: `standard` (default, full workflow) or `simple` (markdown-only lifecycle). Persisted to `.issueflows/config.toml`; `update` honours it. See [Modes](#modes). |
| `--skill-level`    | Skill level — controls quality-tooling recommendations: `basic` (minimal), `standard` (default), `advanced` (opinionated type checking / linting / pre-commit guidance). Persisted to `.issueflows/config.toml`; `update` honours it. See [Skill levels](#skill-levels). |


Running `init` again without `--force` is safe: generated scaffold files that already exist are skipped, and **issue markdown under `.issueflows/` is never touched** by `init` or `update`. The project brief at `.issueflows/04-designs-and-guides/this-project.md` is also user-owned: `init` creates it only when missing, even with `--force`. When the CLI detects an existing scaffold, it reminds you about `update` and `--force`.

### `issue-flow update`


| Argument / Option  | Description                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROJECT_DIR`      | Project root directory. Defaults to `.` (current directory).                                                                                      |
| `--skip-dep-check` | Skip the external-CLI dependency check (`git`, `gh`) and the confirmation prompt that follows if anything is missing.                             |
| `--editor`, `-e`   | AI coding tool(s) to refresh for: `cursor` (default), `claude`, `opencode`, `codex`, or `all`. Repeatable. See [Editor support](#editor-support). |


Use `update` after upgrading the **issue-flow** package to refresh the packaged skills, command files where supported, rules file(s), and `docs/issue-workflow.md` from the version you have installed. This **overwrites** those generated files (unlike a plain second `init`) and prunes retired generated command/skill files. It still does not modify arbitrary files under `.issueflows/` (for example your `issue*_original.md` / `issue*_status.md` files), and it creates any **new** `.issueflows/` subdirectories required by the current package. If `.issueflows/04-designs-and-guides/this-project.md` is missing, `update` recreates the starter brief; if it exists, user content is preserved. `update` also respects the project's persisted [mode](#modes): it refreshes only that mode's surfaces (and prunes any that the mode excludes). To change mode, re-run `issue-flow init --mode <id>`.

### `issue-flow graphify`


| Argument / Option               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `-C`, `--project-dir`           | Project root directory to scan with graphify. Defaults to `.` (current directory). Modeled on `git -C` so positional args can flow into graphify untouched.                                                                                                                                                                                                                                                                                                                                                                                                              |
| `...graphify subcommand + args` | Optional graphify subcommand + flags. With no extras runs `graphify update <PROJECT_DIR>` — AST-only, **no LLM API key required**. The first extra arg, if it is a recognized build subcommand (`update`, `extract`, `watch`, `cluster-only`, `check-update`), picks the action; trailing tokens forward verbatim. Examples: `issue-flow graphify extract` (semantic LLM pass; needs `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `MOONSHOT_API_KEY` or `--backend ollama`), `issue-flow graphify cluster-only --no-viz`, `issue-flow graphify ./subdir`. |


`graphify` requires `graphifyy` to be installed (`uv tool install graphifyy`). When the `graphify` CLI is missing, the command prints install hints and exits with code `2`. Outputs land in `graphify-out/` (`graph.html`, `GRAPH_REPORT.md`, `graph.json`).

### `issue-flow status`

A **read-only** overview of where every issue stands — the same picture the
`/iflow-status` skill produces, but computed deterministically in Python. It
reports the focus issue and its lifecycle stage, parked work, the solved-issue
count, and (unless `--local`) open GitHub issues cross-referenced against your
local `.issueflows/` folders.


| Argument / Option | Description                                                                       |
| ----------------- | --------------------------------------------------------------------------------- |
| `PROJECT_DIR`     | Project root directory. Defaults to `.` (current directory).                      |
| `--local`         | Skip the GitHub query; report only the local `.issueflows/` state.                |
| `--json`          | Emit a machine-readable JSON object instead of the human-readable text report.    |


A missing or unauthenticated `gh` never fails the command — the GitHub section
is simply skipped and noted.

### `issue-flow agent ...`

The `agent` sub-app exposes the deterministic, mechanical building blocks the
scaffolded skills repeat over and over, so an AI agent can ask the tool for an
answer (ideally with `--json`) instead of re-deriving lifecycle state by hand.
The scaffolded skills/commands use these as an **optional fast path** and fall
back to their manual steps when the CLI is not installed, so nothing breaks if a
project never installs `issue-flow`.


| Command                  | What it does                                                                                                                                       |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent state`            | Resolve the focus issue (branch-derived number wins, else the single current group), its lifecycle stage (`init`/`plan`/`start`/`close`), and the suggested next command. |
| `agent preflight`        | Branch hygiene report: default branch, clean/dirty working tree, ahead/behind vs `origin/<default>`, and a stale-branch flag when the issue is already archived. Runs `git fetch --prune` first. |
| `agent sweep`            | Archive `issue<N>_*` groups out of `01-current-issues/` to `03-solved-issues/` (Done) or `02-partly-solved-issues/` (not Done). Use `--except N` to keep the focus issue and `--dry-run` to preview. |
| `agent capture N`        | Fetch GitHub issue `N` with `gh` and write `issue<N>_original.md` (the `## Original issue text` body). Prints the comments payload so the agent can triage them; comment triage stays agent-side. Use `--repo`, `--force`, `-C`. |


All `agent` commands accept `--json` and degrade gracefully: read-only commands
never hard-fail when `git`/`gh` is missing (they return partial data with a
note), while `agent capture` needs `gh` and exits non-zero with a hint when it
is unavailable or the fetch fails.

### When to use which


| Goal                                                                 | Command                   |
| -------------------------------------------------------------------- | ------------------------- |
| First-time setup, or add missing files only                          | `issue-flow init`         |
| Pull newer templates after `uv tool upgrade issue-flow` (or similar) | `issue-flow update`       |
| Replace generated scaffolds without upgrading logic                  | `issue-flow init --force` |
| Rebuild the graphify knowledge graph                                 | `issue-flow graphify`     |
| See where every issue stands (focus / parked / solved / GitHub)      | `issue-flow status`       |
| Let an agent resolve lifecycle state / sweep / capture deterministically | `issue-flow agent ...`    |


## Modes

A **mode** selects which workflow surfaces (skills / slash commands) `init`
installs, so you can scaffold a lighter workflow when the full lifecycle is more
than you need. Two modes ship built in:

| Mode | What you get |
| --- | --- |
| `standard` (default) | The full workflow: planning, PRs, history, cleanup, graphify, and all helpers. |
| `simple` | A markdown-only lifecycle (capture, plan, implement, park, status). No PR/cleanup/yolo/fix/graphify automation. |

```bash
issue-flow init --mode simple
```

The chosen mode is **persisted** to `.issueflows/config.toml`
(`[issueflow].mode`), so `issue-flow update` refreshes exactly that mode's
surfaces. `update` never changes the mode — switch by re-running `init --mode
<id>` (which also prunes the surfaces the new mode drops). The active mode
resolves in this order: **`--mode` (CLI, on `init`)** > **`.issueflows/config.toml`**
(the persisted choice) > **`ISSUEFLOW_MODE`** (env, a fallback for projects that
haven't persisted a mode) > **`standard`**. The persisted choice deliberately
beats the environment, so a stray `ISSUEFLOW_MODE` can't silently override your
project's mode on `update`.

**Custom modes.** A project can define its own modes in
`.issueflows/config.toml` using `[modes.<id>]` tables — either explicit
`skills`/`commands` lists or `extends` + `add`/`remove` to compose on top of a
built-in mode (a mode may reference any surface issue-flow ships):

```toml
[issueflow]
mode = "mine"

[modes.mine]
name = "Mine"
extends = "simple"
add = ["iflow_graphify"]
```

**Caveman skill.** The `standard` mode also installs an optional `caveman` Agent
Skill (`<agent_dir>/skills/caveman/`) — a terse, "token-greedy" response style
that keeps technical substance but drops filler. It is off by default and only
activates when you ask for it ("caveman" / "token greedy"); turn it off with
"stop caveman" or "normal mode". The lightweight `simple` mode omits it.

To make caveman **on by default for a project**, set `caveman_default = true`
under `[issueflow]` in `.issueflows/config.toml` and re-run `issue-flow update`:

```toml
[issueflow]
caveman_default = true
```

This renders an always-on caveman pointer into the managed rule body (so the
always-applied rule re-arms it every session); you can still drop it for the rest
of a session with "stop caveman" / "normal mode". The flag is only honored when
the `caveman` skill is part of the active mode. It resolves in the order
`config.toml` > `ISSUEFLOW_CAVEMAN_DEFAULT` (env) > `false`; the persisted value
beats the env var so a stray env can't flip it on `update`.

**Grill-me skill.** The `standard` mode also installs a `grill-me` Agent Skill
(`<agent_dir>/skills/grill-me/`) — a relentless planning interview that
stress-tests a plan or design (one question at a time, each with a recommended
answer) until every branch of the decision tree is resolved, then feeds the
conclusions into `issue<N>_plan.md`. It is off by default and only activates when
you ask for it ("grill me"); turn it off with "stop grilling" or "normal mode".
The lightweight `simple` mode omits it.

To make grilling **on by default during planning for a project**, set
`grill_me_default = true` under `[issueflow]` in `.issueflows/config.toml` and
re-run `issue-flow update`:

```toml
[issueflow]
grill_me_default = true
```

This renders an always-on grill-me pointer into the managed rule body and the
`/iflow-plan` skill, so planning starts with a grilling pass every session; you
can still drop it for the rest of a session with "stop grilling" / "normal mode".
The flag is only honored when the `grill_me` skill is part of the active mode. It
resolves in the order `config.toml` > `ISSUEFLOW_GRILL_ME_DEFAULT` (env) >
`false`; the persisted value beats the env var so a stray env can't flip it on
`update`.

**Label-driven flows.** Issue labels can select the flow: when an issue picked
via `/iflow-pick` carries the **`yolo`** label, it is routed through the
hands-off `/iflow-yolo` chain (one combined confirmation covering the branch and
the whole `init → plan → start → close yolo` run, which merges the PR and pulls
the default branch at the end). This is **on by default** and controlled by two
keys under `[issueflow]` in `.issueflows/config.toml`:

```toml
[issueflow]
label_flows = true    # allow labels to select the flow (default: true)
yolo_label = "yolo"   # the label that triggers the yolo flow (default: "yolo")
```

Set `label_flows = false` to opt out, or change `yolo_label` to use a different
trigger label; re-run `issue-flow update` after changing either so the commands
re-render. Each resolves in the order `config.toml` > env
(`ISSUEFLOW_LABEL_FLOWS` / `ISSUEFLOW_YOLO_LABEL`) > default (`true` / `"yolo"`);
persisted values beat the env vars. Only honored when the `iflow-pick` and
`iflow-yolo` commands are part of the active mode.


## Editor support

issue-flow can scaffold its workflow for several AI coding tools. Pass one or
more `--editor` values (repeatable, or `all`) to `init` / `update`; the default
is `cursor`, so existing setups are unchanged.

```bash
issue-flow init                          # Cursor (default)
issue-flow init --editor claude          # Claude Code
issue-flow init -e cursor -e claude      # both
issue-flow init --editor all             # every supported editor
```

**Agent Skills** (`<agent_dir>/skills/<name>/SKILL.md`) are the portable core —
every editor gets the full set. **`AGENTS.md`** is the convergent rules file and
is written for every editor as a non-destructive *managed block* (issue-flow
only ever owns the content between its markers, so a hand-maintained `AGENTS.md`
is preserved). Slash commands and an editor-specific rules file are layered on
top where the tool supports them.


| Editor      | `agent_dir`  | Slash commands | Skills | Extra rules file                    | `AGENTS.md` | graphify auto-register |
| ----------- | ------------ | -------------- | ------ | ----------------------------------- | ----------- | ---------------------- |
| Cursor      | `.cursor/`   | — (use skills) | yes    | `.cursor/rules/issueflow-rules.mdc` | yes         | yes                    |
| Claude Code | `.claude/`   | `commands/`    | yes    | `CLAUDE.md`                         | yes         | no                     |
| opencode    | `.opencode/` | `command/`     | yes    | —                                   | yes         | no                     |
| Codex       | `.codex/`    | — (use skills) | yes    | —                                   | yes         | no                     |


Cursor and Codex use skills as their primary slash-menu surface, so you invoke
the mirrored skills (e.g. `/iflow-init`) instead of separate files under
`commands/`. `issue-flow update` removes known generated `.cursor/commands/`
files during the Cursor migration but preserves unrelated user commands. The
graphify integration currently registers only with Cursor; other editors still
get the `/iflow-graphify` command/skill where applicable but no automatic
`graphify cursor install`.

## Configuration

issue-flow reads a `.env` file from the project root (.via python-dotenv). `issue-flow init` **creates a starter `.env` when one is missing** (all `ISSUEFLOW_*` lines written commented-out, so nothing is overridden until you uncomment). It never replaces an existing `.env` — not even with `--force`; on later runs it only *appends* commented hints for any `ISSUEFLOW_*` keys you don't already have. `issue-flow update` does not touch `.env` at all. The following environment variables are supported:


| Variable                 | Default        | Description                                                                                                                                   |
| ------------------------ | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `ISSUEFLOW_DIR`          | `.issueflows`  | Name of the issue-tracking directory.                                                                                                         |
| `ISSUEFLOW_EDITOR`       | `cursor`       | Default editor profile when `--editor` is not passed (`cursor`, `claude`, `opencode`, `codex`).                                               |
| `ISSUEFLOW_AGENT_DIR`    | *(per editor)* | Override the agent/IDE config directory. When unset it is derived from the editor profile (e.g. `.cursor`, `.claude`, `.opencode`, `.codex`). |
| `ISSUEFLOW_DOCS_DIR`     | `docs`         | Where to write the workflow documentation file.                                                                                               |
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md`   | Changelog file that `/iflow-close` updates (set to e.g. `CHANGELOG.md` for different conventions).                                            |
| `ISSUEFLOW_MODE`         | `standard`     | Fallback [scaffolding mode](#modes) when none is persisted in `.issueflows/config.toml`. The canonical store is `config.toml` (written by `init --mode`), which **takes precedence over this env var**. Full order: `--mode` (CLI) > `config.toml` > `ISSUEFLOW_MODE` > `standard`. |
| `ISSUEFLOW_SKILL_LEVEL`  | `standard`     | Fallback [skill level](#skill-levels) when none is persisted in `.issueflows/config.toml`. The canonical store is `config.toml` (written by `init --skill-level`), which **takes precedence over this env var**. Full order: `--skill-level` (CLI) > `config.toml` > `ISSUEFLOW_SKILL_LEVEL` > `standard`. |
| `ISSUEFLOW_CAVEMAN_DEFAULT` | `false`     | Fallback for the [always-on caveman](#modes) toggle when `[issueflow].caveman_default` is not persisted in `.issueflows/config.toml`. The persisted value takes precedence. Full order: `config.toml` > `ISSUEFLOW_CAVEMAN_DEFAULT` > `false`. Only honored when the `caveman` skill is in the active mode. |
| `ISSUEFLOW_GRILL_ME_DEFAULT` | `false`    | Fallback for the [grill-me-during-planning](#modes) toggle when `[issueflow].grill_me_default` is not persisted in `.issueflows/config.toml`. The persisted value takes precedence. Full order: `config.toml` > `ISSUEFLOW_GRILL_ME_DEFAULT` > `false`. Only honored when the `grill_me` skill is in the active mode. |
| `ISSUEFLOW_LABEL_FLOWS`  | `true`         | Fallback for the [label-driven flows](#modes) toggle when `[issueflow].label_flows` is not persisted in `.issueflows/config.toml`. The persisted value takes precedence. Full order: `config.toml` > `ISSUEFLOW_LABEL_FLOWS` > `true`. Only honored when the `iflow-pick` and `iflow-yolo` commands are in the active mode. |
| `ISSUEFLOW_YOLO_LABEL`   | `yolo`         | Fallback for the [yolo trigger label](#modes) when `[issueflow].yolo_label` is not persisted in `.issueflows/config.toml`. The persisted value takes precedence. Full order: `config.toml` > `ISSUEFLOW_YOLO_LABEL` > `yolo`. |

Beyond the `ISSUEFLOW_*` settings above, `issue-flow graphify` also reads an LLM
API key from `.env` when present (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, or `MOONSHOT_API_KEY`) and passes it through to the
`graphify extract` semantic pass. The no-arg `graphify update` build is
AST-only and needs no key.

### Creating `config.toml`

`init --mode <id>` is the usual way `.issueflows/config.toml` first appears, but
you can also materialize a fully-commented file on demand:

```bash
issue-flow config add            # create .issueflows/config.toml if missing
issue-flow config add --force    # regenerate its [issueflow] keys in place
```

It writes the six keys issue-flow actually reads from `config.toml` — `mode`,
`skill_level`, `caveman_default`, `grill_me_default`, `label_flows`,
`yolo_label` — taking each value from its `ISSUEFLOW_*` env var / `.env` when
set, otherwise the issue-flow default (`standard`, `standard`, `false`, `false`,
`true`, `"yolo"`). The other `ISSUEFLOW_*` settings are **environment-only** and
are deliberately *not* written to `config.toml` (putting them there would have no
effect). An existing file is left untouched unless `--force` is passed, in which
case the six keys are upserted while your comments and `[modes.*]` tables are
preserved. After changing `caveman_default` / `grill_me_default` /
`label_flows` / `yolo_label`, re-run `issue-flow update` so the rule and
commands re-render. Pass `--json` for a machine-readable result.


## Development

```bash
git clone https://github.com/jepegit/issue-flow.git
cd issue-flow
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/
```

## Changelog

See [HISTORY.md](HISTORY.md) for release notes.

## Future plans

- **More editors** — extend `--editor` coverage to further AI coding tools (e.g. Windsurf) on top of the current Cursor / Claude Code / opencode / Codex support.
- **Custom templates** — let users supply their own Jinja2 templates to tailor slash commands and rules to their team's conventions.
- **Git hook integration** — optionally move issue files on commit based on status markers.
- **GitHub Actions workflow** — ship a reusable action that syncs issue state between `.issueflows/` and GitHub issue labels/milestones.

## Acknowledgements

issue-flow builds on and takes inspiration from other people's open-source work.
Thanks to the authors and communities behind these projects:

| Project | How issue-flow uses it | License |
| --- | --- | --- |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Inspiration for the bundled `caveman` Agent Skill (terse, token-greedy response style). Our version is a trimmed adaptation — full intensity only, English only. | [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE) |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock's `grill-me` skill inspired the bundled `grill-me` Agent Skill (relentless planning interview). Our version is adapted to issue-flow's planning workflow, feeding conclusions into `issue<N>_plan.md`. | [MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) |
| [safishamsi/graphify](https://github.com/safishamsi/graphify) (`graphifyy` on PyPI) | Powers the optional knowledge-graph integration (`issue-flow graphify`, `graphify-out/`). Installed separately and invoked as an external tool. | [MIT](https://github.com/safishamsi/graphify/blob/main/LICENSE) |
| [Typer](https://github.com/fastapi/typer) | The `issue-flow` command-line interface. | MIT |
| [Rich](https://github.com/Textualize/rich) | Formatted terminal output during `init` / `update`. | MIT |
| [Jinja2](https://github.com/pallets/jinja) | Renders the scaffolded skill, command, and rules templates. | BSD-3-Clause |
| [tomlkit](https://github.com/python-poetry/tomlkit) | Comment-preserving round-trips of `.issueflows/config.toml`. | MIT |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads `ISSUEFLOW_*` settings from a project `.env`. | BSD-3-Clause |

Using or drawing on another project that should be listed here? Open a PR or issue
to add a row.

## License

This project is released under the MIT License. See the full text in the repository: [LICENSE](https://github.com/jepegit/issue-flow/blob/main/LICENSE).