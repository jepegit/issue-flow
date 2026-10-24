# issue-flow

[![PyPI](https://img.shields.io/pypi/v/issue-flow.svg)](https://pypi.org/project/issue-flow/)
[![Documentation Status](https://readthedocs.org/projects/issue-flow/badge/?version=latest)](https://issue-flow.readthedocs.io/en/latest/?badge=latest)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/issue-flow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/issue-flow)

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project so that AI coding agents can pick up GitHub issues, plan work, and land PRs in a consistent way. It supports **Cursor, Claude Code, opencode, and Codex** via `--editor` (see [Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md)); the examples below use the default, Cursor.

**Full documentation:** <https://issue-flow.readthedocs.io/>


## Why use it

Every change starts from a GitHub issue, gets a written plan that **you approve before any code is touched**, and lands as a pull request with a changelog entry. The state of each issue is kept in plain markdown files in your repository, so the work survives across chat sessions and the next agent can pick it up.

It may slow you down a little compared with letting an agent loose. Maybe that is a good thing.


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
    05-epics/               # Staged epic plans (epic<N>_plan.md)
  .cursor/
    skills/                  # Agent Skills: 11 commands; each folder holds
                             # SKILL.md plus mode files (yolo.md, epic.md, …)
    rules/
      issueflow-rules.mdc    # Cursor pointer to the AGENTS.md block
  AGENTS.md                  # Workflow rules (managed block; shared by all editors)
  docs/
    issue-workflow.md        # Human-readable overview of the workflow
```

The exact `agent_dir` and the per-editor rules file depend on which editor(s) you scaffold for — see [Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md). `AGENTS.md` (written as a non-destructive managed block), `.issueflows/04-designs-and-guides/this-project.md` (a hand-editable project brief created only when missing), and `docs/issue-workflow.md` are shared by every editor.

The Agent Skills give agents a repeatable flow and appear in the slash menu. In chat you can also type **`iflow plan`**, **`iflow pick 42`**, etc. (space-separated, no `/`) when your keyboard makes slash awkward. The linear path is:

1. `/iflow-pick` (or `iflow pick 42`) — chooses an issue, creates its branch or worktree, and captures it into `.issueflows/01-current-issues/`.
2. `/iflow-plan` — drafts `issue<N>_plan.md` and stops for your confirmation.
3. `/iflow-build` — implements the confirmed plan.
4. `/iflow-close` — runs tests, optionally bumps the version, adds changelog trailers to the commit, updates status files, commits, pushes, and opens a PR.
5. `/iflow-cleanup` — after the PR merges, switches to the default branch, pulls, and deletes landed local branches behind explicit confirms.

`/iflow` runs whichever of these is next for the focus issue. The full surface is eleven commands; the merged ones take a **mode** as their first word, and each mode's instructions live in a separate file inside the skill folder, so an agent reads only what it needs:

| Command | Modes | What it does |
|---|---|---|
| `/iflow` | — | Dispatcher: run the next of capture / plan / build / close. |
| `/iflow-setup` | `harness`, `check` | Get a project ready (uv, git, GitHub, scaffold). |
| `/iflow-pick` | `<N>`, `capture`, `fix`, `label:<L>` | Choose an issue, branch, and capture it. |
| `/iflow-plan` | — | Write the plan and stop for approval. |
| `/iflow-build` | — | Implement the approved plan. |
| `/iflow-pause` | — | Park unfinished work with resume notes. |
| `/iflow-close` | `yolo`, `ops`, `draft`, `bump` | Tests, bump, changelog trailers, commit, push, PR. |
| `/iflow-cleanup` | `all`, `github`, `prs`, `archive` | After merge: default branch, pull, delete landed branches. |
| `/iflow-run` | `yolo`, `cycle`, `auto`, `drive` | Hands-off runs under one up-front confirm. |
| `/iflow-issue` | `fix`, `epic`, `split`, `review` | Create and shape GitHub issues. |
| `/iflow-status` | `doctor`, `git`, `graph` | Read-only overview of every issue. |

See the [docs](https://issue-flow.readthedocs.io/) for worked recipes (review → cycle, epic publish, cycle queues).

## Prerequisites

issue-flow itself is a small Python CLI, but the **scaffolded commands and skills
it writes into your project shell out to a few external tools**. If they are
missing, the workflows will fail at runtime — so `issue-flow init` now
checks for them up front and prints install hints before it does anything.

Required:

- **[Git](https://git-scm.com/downloads)** — used by every slash command for
branch, fetch, status, commit, and push operations. Almost certainly already
installed if you're here, but the check covers it for completeness.
- **[GitHub CLI (`gh`)](https://cli.github.com/)** — used by `/iflow-pick` to
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

### Multi-root workspaces

Parent folder of several git repos? Do not `init` the parent. From that folder:

```bash
issue-flow workspace bootstrap --yes --default <main-repo>   # first time
issue-flow workspace update                                  # later refreshes
```

Repos already scaffolded, toml missing: `issue-flow workspace init --default <main-repo>` then `workspace update`.

Recipe: [Use issue-flow in a folder of repos](docs/how-to/workspaces.md).

Lifecycle commands must still target the correct repo (`root:` / `repo:` hints, or `issue-flow agent resolve`). See `.issueflows/04-designs-and-guides/workspaces.md#multi-repo-workspaces` in scaffolded projects.

### Optional: graphify integration

issue-flow has a lightweight integration with [graphify](https://graphify.net)
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
- The `/iflow-status graph` mode wraps
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
- The scaffolded rules and `/iflow-build` mention `graphify-out/GRAPH_REPORT.md`
as a recommended pre-read when the file exists. Nothing rebuilds the graph
automatically unless you set `auto_graphify_on_plan`.

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
> venv but leaves the `graphify` CLI invisible to the shell, so `/iflow-status graph`
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

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/) (recommended).

```bash
uv tool install issue-flow
```

Or add it as a dev dependency to your project: `uv add --dev issue-flow`.

The scaffolded workflows shell out to **[Git](https://git-scm.com/downloads)** and the **[GitHub CLI (`gh`)](https://cli.github.com/)** (run `gh auth login` once after installing). `issue-flow init` checks for both up front and prints install hints before it does anything; bypass the prompt in automation with `--skip-dep-check`.

## Quick start

```bash
cd your-project
issue-flow init
```

That's it. Open the project in your editor and, in the chat window:

| Type this | What happens |
|---|---|
| `iflow pick` | Shows you the open GitHub issues, you choose one, it creates a branch |
| `iflow plan` | Writes a plan and **stops** for you to approve it |
| `iflow build` | Implements the approved plan |
| `iflow close` | Runs tests, writes changelog trailers into the commit, commits, pushes, opens a pull request |
| `iflow cleanup` | After the PR is merged: back to the main branch, tidy up local branches |

Forgot where you are? Type `iflow` and it runs the next step. (Slash forms
such as `/iflow-plan` work too.)

> **New to agentic coding, or starting from an empty folder?** Use
> `issue-flow init --mode novice` instead — a smaller command surface with
> settings that stop and ask at each step — then type `iflow setup` in the chat
> window and the agent walks you through `uv init`, `git init`, `gh auth login`,
> and creating the GitHub repository. See
> [Getting started](https://issue-flow.readthedocs.io/en/latest/getting-started/).

Everything else lives in the merged commands: `iflow run yolo 42` for a small issue in one go, `iflow issue epic 42` to stage a big change, `iflow status doctor` to check the tracking folders, and so on. The table under [What it does](#what-it-does) lists every command and mode.

Docs cover epics, cycles, and reviews with examples:
https://issue-flow.readthedocs.io/

## CLI overview

```
issue-flow init [PROJECT_DIR] [--force] [--skip-dep-check] [--editor EDITOR] [--mode MODE] [--skill-level LEVEL] [--install-hooks]
issue-flow update [PROJECT_DIR] [--skip-dep-check] [--editor EDITOR]
issue-flow graphify [-C PROJECT_DIR] [...graphify subcommand + args]
issue-flow status [PROJECT_DIR] [--local] [--json]
issue-flow agent state|preflight|switchback|resolve|sweep|archive|capture [...]
issue-flow config add [-C PROJECT_DIR] [--force] [--json]
issue-flow hooks install|uninstall|status|run [pre-commit] [-C PROJECT_DIR]
issue-flow workspace bootstrap|init|update [WORKSPACE_DIR] [...]
```

- `init` scaffolds; running it again without `--force` only adds missing files.
- `update` refreshes generated files after upgrading the package (overwrites scaffolds, never your issue markdown).
- `workspace bootstrap` / `init` / `update` cover a **parent folder of sibling repos** (see [how-to](docs/how-to/workspaces.md)).
- `status` / `agent ...` give agents (and you) **deterministic** answers about lifecycle state — focus issue, stage, branch hygiene — instead of having the agent re-derive it by hand.
- `hooks install` (or `init --install-hooks`) adds an **opt-in** git `pre-commit` hook that moves issue groups marked `- [x] Done` to `03-solved-issues/` and stages the move in the same commit. It never blocks a commit; see the [CLI reference](https://github.com/jepegit/issue-flow/blob/main/docs/cli.md#issue-flow-hooks) for Husky / pre-commit setups and how to disable it.
- `issue-flow --install-completion` enables Tab completion for subcommands (bash / zsh / fish).

Full option tables and the `agent` subcommand reference live in the [CLI reference](https://github.com/jepegit/issue-flow/blob/main/docs/cli.md).

## Going further

- **[Configuration](https://github.com/jepegit/issue-flow/blob/main/docs/configuration.md)** — `.env` variables and `.issueflows/config.toml`; **modes** (`standard` vs the markdown-only `simple`), **skill levels** (`basic` / `standard` / `advanced` quality-tooling guidance), the optional **caveman** and **grill-me** skills, the opt-in vendored **pstack** skills (`pstack_skills`), and **label-driven flows** (a `yolo` label routes an issue through the hands-off chain).
- **[Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md)** — what gets scaffolded per editor (Cursor, Claude Code, opencode, Codex), and how multi-root workspaces resolve the right repo.
- **[Folder of repos](https://github.com/jepegit/issue-flow/blob/main/docs/how-to/workspaces.md)** — `workspace bootstrap` / `init` / `update` from a parent folder.
- **[Graphify integration](https://github.com/jepegit/issue-flow/blob/main/docs/graphify.md)** — optional knowledge graph of your codebase that agents can read instead of grepping; enabled simply by installing `graphifyy`.
- **[Issue workflow](https://github.com/jepegit/issue-flow/blob/main/docs/issue-workflow.md)** — the human-readable walkthrough of the full lifecycle (also scaffolded into your project).

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

See [docs/developing.md](https://github.com/jepegit/issue-flow/blob/main/docs/developing.md) for more.

## Changelog

See [HISTORY.md](https://github.com/jepegit/issue-flow/blob/main/HISTORY.md) for release notes.

## GitHub Actions sync

Sync `.issueflows/` folder placement (`01-current-issues` / `02-partly-solved-issues` /
`03-solved-issues`) to GitHub issue labels (one-way: files → GitHub).

**CLI (local or CI):**

```bash
issue-flow sync              # dry-run (shows planned label changes)
issue-flow sync --apply      # push labels via gh
issue-flow sync --json       # machine-readable report
```

**Managed labels** (default prefix `status:`): `status:current`, `status:parked`,
`status:solved`. Only labels with that prefix are added/removed; other labels
(e.g. `yolo`) are left alone.

**Bootstrap labels once** (if they do not exist yet):

```bash
gh label create 'status:current' --color 0E8A16
gh label create 'status:parked' --color FBCA04
gh label create 'status:solved' --color 6E7781
```

By default, `issue-flow sync --apply` **auto-creates** any missing managed labels
(`bootstrap_labels = true` in `[issueflow.sync]`). Set `bootstrap_labels = false`
to keep the manual-only behaviour.

**Configuration** — optional `[issueflow.sync]` in `.issueflows/config.toml`:

```toml
[issueflow.sync]
enabled = true
label_prefix = "status:"
labels = true
milestones = false
close_on_solved = false
bootstrap_labels = true

[issueflow.sync.milestone_map]
current = ""
parked = ""
solved = ""
```

**Reusable workflow** — add a caller in your repo (pin to a release tag):

```yaml
on:
  push:
    paths: ['.issueflows/**']
jobs:
  sync:
    uses: jepegit/issue-flow/.github/workflows/issue-flow-sync.yml@v0.4.4
    with:
      dry_run: false
    secrets: inherit
```

Requires `permissions: issues: write` on the job. The workflow installs
`issue-flow` from PyPI by default (`install_mode: pypi`); this repo dogfoods
with `install_mode: workspace` via [`.github/workflows/issueflow-sync.yml`](.github/workflows/issueflow-sync.yml).

## Future plans

- **More editors** — extend `--editor` coverage to further AI coding tools (e.g. Windsurf) on top of the current Cursor / Claude Code / opencode / Codex support.
- **Custom templates** — let users supply their own Jinja2 templates to tailor slash commands and rules to their team's conventions.

## Acknowledgements

issue-flow builds on and takes inspiration from other people's open-source work.
Thanks to the authors and communities behind these projects:

| Project | How issue-flow uses it | License |
| --- | --- | --- |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Inspiration for the bundled `caveman` Agent Skill (terse, token-greedy response style). Our version is a trimmed adaptation — full intensity only, English only. | [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE) |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock's `grill-me` skill inspired the bundled `grill-me` Agent Skill (relentless planning interview). Our version is adapted to issue-flow's planning workflow, feeding conclusions into `issue<N>_plan.md`. | [MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) |
| [cursor/plugins — pstack](https://github.com/cursor/plugins/tree/main/pstack) | Lauren Tan's (poteto) `pstack` skills library. A curated subset of its single-file skills (`unslop`, `tdd`, `blast-radius`, `technical-writing`, `bro`, four `principle-*` skills) is vendored **verbatim** as opt-in templates (`pstack_skills` in `config.toml`); the upstream MIT text ships alongside. | [MIT](https://github.com/cursor/plugins/blob/main/pstack/LICENSE) |
| [safishamsi/graphify](https://github.com/safishamsi/graphify) (`graphifyy` on PyPI) | Powers the optional knowledge-graph integration (`issue-flow graphify`, `graphify-out/`). Installed separately and invoked as an external tool. | [MIT](https://github.com/safishamsi/graphify/blob/main/LICENSE) |
| [Typer](https://github.com/fastapi/typer) | The `issue-flow` command-line interface. | MIT |
| [Rich](https://github.com/Textualize/rich) | Formatted terminal output during `init` / `update`. | MIT |
| [Jinja2](https://github.com/pallets/jinja) | Renders the scaffolded skill, command, and rules templates. | BSD-3-Clause |
| [tomlkit](https://github.com/python-poetry/tomlkit) | Comment-preserving round-trips of `.issueflows/config.toml`. | MIT |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads `ISSUEFLOW_*` settings from a project `.env`. | BSD-3-Clause |
| [Zensical](https://github.com/zensical/zensical) | Builds the [documentation site](https://issue-flow.readthedocs.io/) (from the Material for MkDocs team). | MIT |

Using or drawing on another project that should be listed here? Open a PR or issue
to add a row.

## License

This project is released under the MIT License. See the full text in the repository: [LICENSE](https://github.com/jepegit/issue-flow/blob/main/LICENSE).
