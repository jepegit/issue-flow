# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project so that AI coding agents can pick up GitHub issues, plan work, and land PRs in a consistent way. It supports **Cursor, Claude Code, opencode, and Codex** via `--editor` (see [Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md)); the examples below use the default, Cursor.

**Full documentation:** <https://issue-flow.readthedocs.io/>

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
    skills/                  # Agent Skills (/iflow, /iflow-pick, /iflow-init,
                             # /iflow-plan, /iflow-start, /iflow-close, ...)
    rules/
      issueflow-rules.mdc    # Always-on Cursor rule for the workflow
  AGENTS.md                  # Workflow rules (managed block; shared by all editors)
  docs/
    issue-workflow.md        # Human-readable overview of the workflow
```

The exact `agent_dir` and the per-editor rules file depend on which editor(s) you scaffold for — see [Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md). `AGENTS.md` (written as a non-destructive managed block), `.issueflows/04-designs-and-guides/this-project.md` (a hand-editable project brief created only when missing), and `docs/issue-workflow.md` are shared by every editor.

The Cursor Agent Skills give agents a repeatable flow and appear in the slash menu. In chat you can also type **`iflow plan`**, **`iflow pick`**, etc. (space-separated, no `/`) when your keyboard makes slash awkward — see `docs/issue-workflow.md`. The linear path is:

1. `/iflow-init 42` or `iflow init 42` — pulls GitHub issue #42 into `.issueflows/01-current-issues/` and archives older issues.
2. `iflow plan` or `/iflow-plan` — drafts `issue<N>_plan.md` (Goal / Constraints / Approach / Files to touch / Test strategy / Open questions) and stops for your confirmation.
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
- `/iflow-archive` — **condense the solved archive (destructive, gated)**: summarises selected `issue<N>_*` groups under `03-solved-issues/` into a dated `YYYY-MM-DD_archived_issues.md` file. The summary records the pre-archive git ref so every original file stays recoverable (`git show <ref>:<path>`). Deletes the source files only after one consolidated confirm. Default: archive all but the **5 most recent** solved groups; pass `keep <K>`, an explicit list of issue numbers, or `all`. Requires a **clean working tree**. Off-path; never auto-dispatched.

The **Agent Skills** under `.cursor/skills/` carry the workflows for on-demand use with `/iflow-pick`, `/iflow`, `/iflow-init`, `/iflow-plan`, `/iflow-start`, `/iflow-pause`, `/iflow-close`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-fix`, `/iflow-status`, `/iflow-archive`, `@iflow-version-bump` when you need only the bump steps, or `@iflow-history-update` when you need only the changelog update (see [Cursor Agent Skills](https://cursor.com/help/customization/skills)).

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

### Multi-root workspaces

When one Cursor workspace contains **several sibling repositories** (each with its
own `issue-flow init`), lifecycle commands must target the correct repo explicitly.
Use slash hints (`root:<path>`, `repo:<folder-name>`, `repo:owner/name`), or run
`issue-flow agent resolve [--from-file <active-file>] [--json]` before `git`/`gh`
calls. See `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` in
scaffolded projects (or run `issue-flow update` to refresh scoped
`issueflow-rules.mdc` files).

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

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/) (recommended).

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

That's it. Open the project in Cursor and start with `/iflow` — or step through the linear path explicitly:

1. `/iflow-init 42` — pulls GitHub issue #42 into `.issueflows/01-current-issues/` and archives older issues.
2. `/iflow-plan` — drafts `issue<N>_plan.md` (Goal / Constraints / Approach / Files to touch / Test strategy / Open questions) and stops for your confirmation.
3. `/iflow-start` — reads the confirmed plan and implements it.
4. `/iflow-close` — runs tests, optionally bumps version, appends a `HISTORY.md` entry, updates status files, commits, pushes, and opens a PR.
5. `/iflow-cleanup` — after the PR merges, switches to the default branch, fast-forwards, prunes, and deletes the merged local branch.

Plus a few off-path commands (never auto-dispatched):

- `/iflow-pick` — **front door**: helps pick the next issue (parked work first, else open GitHub issues ranked by milestone, labels, and similarity to recent work), creates the branch, and runs `/iflow-init`.
- `/iflow` — **quick start**: inspects the current issue's state and dispatches to the right linear step automatically (a branch-derived number like `42-fix-login` is authoritative).
- `/iflow-pause` — park the current issue with a **Remaining work** note.
- `/iflow-yolo` — all-in-one chain (`init → plan → start → close`) for small, low-risk issues, with up-front safeguards and a single consolidated confirm.
- `/iflow-fix` — interactive iterative-fixes session: one GitHub issue + long-lived branch, many small confirmed fixes.
- `/iflow-status` — **read-only** overview of where every issue stands, locally and on GitHub.
- `/iflow-archive` — condense old solved-issue files into a dated summary (destructive, gated behind one consolidated confirm; originals stay recoverable via git).

## CLI overview

```
issue-flow init [PROJECT_DIR] [--force] [--skip-dep-check] [--editor EDITOR] [--mode MODE] [--skill-level LEVEL]
issue-flow update [PROJECT_DIR] [--skip-dep-check] [--editor EDITOR]
issue-flow graphify [-C PROJECT_DIR] [...graphify subcommand + args]
issue-flow status [PROJECT_DIR] [--local] [--json]
issue-flow agent state|preflight|switchback|resolve|sweep|archive|capture [...]
issue-flow config add [-C PROJECT_DIR] [--force] [--json]
```

- `init` scaffolds; running it again without `--force` only adds missing files.
- `update` refreshes generated files after upgrading the package (overwrites scaffolds, never your issue markdown).
- `status` / `agent ...` give agents (and you) **deterministic** answers about lifecycle state — focus issue, stage, branch hygiene — instead of having the agent re-derive it by hand.

Full option tables and the `agent` subcommand reference live in the [CLI reference](https://github.com/jepegit/issue-flow/blob/main/docs/cli.md).

## Going further

- **[Configuration](https://github.com/jepegit/issue-flow/blob/main/docs/configuration.md)** — `.env` variables and `.issueflows/config.toml`; **modes** (`standard` vs the markdown-only `simple`), **skill levels** (`basic` / `standard` / `advanced` quality-tooling guidance), the optional **caveman** and **grill-me** skills, and **label-driven flows** (a `yolo` label routes an issue through the hands-off chain).
- **[Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md)** — what gets scaffolded per editor (Cursor, Claude Code, opencode, Codex), and how multi-root workspaces resolve the right repo.
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
