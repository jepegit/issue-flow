# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project so that Cursor AI agents can pick up GitHub issues, plan work, and land PRs in a consistent way.

## What it does

Running `issue-flow init` in your project root creates:

```text
your-project/
  .issueflows/
    00-tools/                # Helper scripts for agents
    01-current-issues/       # Active issue markdown files
    02-partly-solved-issues/ # Parked / in-progress issues
    03-solved-issues/        # Completed issues archive
  .cursor/
    commands/
      iflow.md               # /iflow — smart dispatcher (quick start)
      issue-init.md          # /issue-init — fetch a GitHub issue locally
      issue-plan.md          # /issue-plan — write issue<N>_plan.md and confirm
      issue-start.md         # /issue-start — implement the plan
      issue-pause.md         # /issue-pause — park work in 02-partly-solved-issues/
      issue-close.md         # /issue-close — test, commit, push, PR
      issue-cleanup.md       # /issue-cleanup — post-merge branch hygiene
      issue-yolo.md          # /issue-yolo — all-in-one for small, low-risk issues
    skills/                  # Optional Agent Skills (explicit / @ invoke)
      issueflow-iflow/SKILL.md
      issueflow-issue-init/SKILL.md
      issueflow-issue-plan/SKILL.md
      issueflow-issue-start/SKILL.md
      issueflow-issue-pause/SKILL.md
      issueflow-issue-close/SKILL.md
      issueflow-issue-cleanup/SKILL.md
      issueflow-issue-yolo/SKILL.md
      issueflow-version-bump/SKILL.md
      issueflow-history-update/SKILL.md
    rules/
      issueflow-rules.mdc    # Always-on Cursor rule for the workflow
  docs/
    cursor-issue-workflow.md # Human-readable overview of the workflow
```

The Cursor slash commands give agents a repeatable flow. The linear path is:

1. `/issue-init 42` — pulls GitHub issue #42 into `.issueflows/01-current-issues/` and archives older issues.
2. `/issue-plan` — drafts `issue<N>_plan.md` (Goal / Constraints / Approach / Files to touch / Test strategy / Open questions) and stops for your confirmation.
3. `/issue-start` — reads the confirmed plan and implements it. If no plan file exists, it offers to run `/issue-plan` first, proceed without a plan, or abort.
4. `/issue-close` — runs tests, optionally bumps version with `uv version --bump`, appends a `HISTORY.md` entry (or promotes `[Unreleased]` to a new release section on a bump), updates status files, commits, pushes, and opens a PR.
5. `/issue-cleanup` — after the PR merges, switches to the default branch, fast-forwards, prunes, and deletes the merged local branch.

Plus a few off-path commands:

- `/iflow` — **quick start**: inspects the current issue's state and dispatches to the right linear step automatically. A branch-derived number (`42-fix-login` → `N=42`) is authoritative, so `/iflow` works from a fresh branch too.
- `/issue-pause` — park the current issue in `02-partly-solved-issues/` with a **Remaining work** note; optional WIP commit + switch back to the default branch.
- `/issue-yolo` — all-in-one chain (`init → plan → start → close`) for small, low-risk issues, with up-front safeguards (refuses on the default branch, refuses with dirty unrelated changes, requires passing tests, single consolidated confirm).

The matching **Agent Skills** (under `.cursor/skills/`) carry the same workflows for on-demand use with `/issueflow-iflow`, `/issueflow-issue-init`, `/issueflow-issue-plan`, `/issueflow-issue-start`, `/issueflow-issue-pause`, `/issueflow-issue-close`, `/issueflow-issue-cleanup`, `/issueflow-issue-yolo`, `@issueflow-version-bump` when you need only the bump steps, or `@issueflow-history-update` when you need only the changelog update (see [Cursor Agent Skills](https://cursor.com/docs/context/skills)).

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

That's it. Open the project in Cursor and start with `/iflow` (or step through `/issue-init`, `/issue-plan`, `/issue-start`, `/issue-close`, `/issue-cleanup` explicitly).

## Usage

```
issue-flow init [PROJECT_DIR] [--force]
issue-flow update [PROJECT_DIR]
```

### `issue-flow init`

| Argument / Option | Description |
|---|---|
| `PROJECT_DIR` | Project root directory. Defaults to `.` (current directory). |
| `--force`, `-f` | Overwrite generated Cursor commands, rules, and workflow doc instead of skipping them. |

Running `init` again without `--force` is safe: generated scaffold files that already exist are skipped, and **issue markdown under `.issueflows/` is never touched** by `init` or `update`. When the CLI detects an existing scaffold, it reminds you about `update` and `--force`.

### `issue-flow update`

| Argument / Option | Description |
|---|---|
| `PROJECT_DIR` | Project root directory. Defaults to `.` (current directory). |

Use `update` after upgrading the **issue-flow** package to refresh the packaged slash commands, Cursor rule, and `docs/cursor-issue-workflow.md` from the version you have installed. This **overwrites** those generated files (unlike a plain second `init`). It still does not modify arbitrary files under `.issueflows/` (for example your `issue*_original.md` / `issue*_status.md` files), and it creates any **new** `.issueflows/` subdirectories required by the current package.

### When to use which

| Goal | Command |
|---|---|
| First-time setup, or add missing files only | `issue-flow init` |
| Pull newer templates after `uv tool upgrade issue-flow` (or similar) | `issue-flow update` |
| Replace generated scaffolds without upgrading logic | `issue-flow init --force` |

## Configuration

issue-flow reads a `.env` file from the project root (via python-dotenv). The following environment variables are supported:

| Variable | Default | Description |
|---|---|---|
| `ISSUEFLOW_DIR` | `.issueflows` | Name of the issue-tracking directory. |
| `ISSUEFLOW_AGENT_DIR` | `.cursor` | Name of the agent/IDE config directory (currently `.cursor`). |
| `ISSUEFLOW_DOCS_DIR` | `docs` | Where to write the workflow documentation file. |
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md` | Changelog file that `/issue-close` updates (set to e.g. `CHANGELOG.md` for different conventions). |

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

- **Multi-tool support** — generate config for other AI coding tools (Claude Code, Windsurf, etc.) in addition to Cursor.
- **`issue-flow status`** — show a dashboard of current, partly-solved, and solved issues.
- **Custom templates** — let users supply their own Jinja2 templates to tailor slash commands and rules to their team's conventions.
- **Git hook integration** — optionally move issue files on commit based on status markers.
- **GitHub Actions workflow** — ship a reusable action that syncs issue state between `.issueflows/` and GitHub issue labels/milestones.

## License

This project is released under the MIT License. See the full text in the repository: [LICENSE](https://github.com/jepegit/issue-flow/blob/main/LICENSE).
