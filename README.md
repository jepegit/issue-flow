# issue-flow

Agents should behave. Let them follow the issue flow.

**issue-flow** scaffolds a lightweight issue-tracking workflow into your project so that Cursor AI agents can pick up GitHub issues, plan work, and land PRs in a consistent way.

## What it does

Running `issue-flow init` in your project root creates:

```text
your-project/
  .issueflows/
    00-tools/               # Helper scripts for agents
    01-current-issues/      # Active issue markdown files
    02-partly-solved-issues/ # Parked / in-progress issues
    03-solved-issues/       # Completed issues archive
  .cursor/
    commands/
      issue-init.md         # /issue-init — fetch a GitHub issue locally
      issue-start.md        # /issue-start — plan and implement
      issue-close.md        # /issue-close — test, commit, push, PR
    rules/
      issueflow-rules.mdc   # Always-on Cursor rule for the workflow
  docs/
    cursor-issue-workflow.md # Human-readable overview of the workflow
```

The three Cursor slash commands give agents a repeatable flow:

1. `/issue-init 42` — pulls GitHub issue #42 into `.issueflows/01-current-issues/` and archives older issues.
2. `/issue-start` — reads the issue file, plans, and implements.
3. `/issue-close` — runs tests, updates status files, commits, pushes, and opens a PR.

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

That's it. Open the project in Cursor and use `/issue-init`, `/issue-start`, `/issue-close`.

## Usage

```
issue-flow init [PROJECT_DIR] [--force]
```

| Argument / Option | Description |
|---|---|
| `PROJECT_DIR` | Project root directory. Defaults to `.` (current directory). |
| `--force`, `-f` | Overwrite existing files instead of skipping them. |

Running `init` a second time is safe — existing files are skipped unless `--force` is passed.

## Configuration

issue-flow reads a `.env` file from the project root (via python-dotenv). The following environment variables are supported:

| Variable | Default | Description |
|---|---|---|
| `ISSUEFLOW_DIR` | `.issueflows` | Name of the issue-tracking directory. |
| `ISSUEFLOW_CURSOR_DIR` | `.cursor` | Name of the Cursor config directory. |
| `ISSUEFLOW_DOCS_DIR` | `docs` | Where to write the workflow documentation file. |

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

## Future plans

- **Multi-tool support** — generate config for other AI coding tools (Claude Code, Windsurf, etc.) in addition to Cursor.
- **`issue-flow status`** — show a dashboard of current, partly-solved, and solved issues.
- **Custom templates** — let users supply their own Jinja2 templates to tailor slash commands and rules to their team's conventions.
- **Git hook integration** — optionally move issue files on commit based on status markers.
- **GitHub Actions workflow** — ship a reusable action that syncs issue state between `.issueflows/` and GitHub issue labels/milestones.

## License

See [LICENSE](LICENSE).
