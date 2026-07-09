# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project so that AI coding agents can pick up GitHub issues, plan work, and land PRs in a consistent way. It supports **Cursor, Claude Code, opencode, and Codex** via `--editor` (see [Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md)); the examples below use the default, Cursor.

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

The exact layout depends on which editor(s) you scaffold for — see [Editor support](https://github.com/jepegit/issue-flow/blob/main/docs/editors.md). Generated files are written non-destructively: `AGENTS.md` is a managed block inside your own file, and issue markdown under `.issueflows/` is never touched by `init` or `update`.

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
