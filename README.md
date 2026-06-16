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
  .cursor/
    commands/
      issue-pick.md          # /issue-pick — choose the next issue, branch, init (front door)
      iflow.md               # /iflow — smart dispatcher (quick start)
      issue-init.md          # /issue-init — fetch a GitHub issue locally
      issue-plan.md          # /issue-plan — write issue<N>_plan.md and confirm
      issue-start.md         # /issue-start — implement the plan
      issue-pause.md         # /issue-pause — park work in 02-partly-solved-issues/
      issue-close.md         # /issue-close — test, commit, push, PR
      issue-cleanup.md       # /issue-cleanup — post-merge branch hygiene
      issue-yolo.md          # /issue-yolo — all-in-one for small, low-risk issues
      issue-fix.md           # /issue-fix — interactive iterative-fixes session
      graphify.md            # /graphify — rebuild the graphify knowledge graph (optional)
    skills/                  # Optional Agent Skills (explicit / @ invoke)
      issueflow-issue-pick/SKILL.md
      issueflow-iflow/SKILL.md
      issueflow-issue-init/SKILL.md
      issueflow-issue-plan/SKILL.md
      issueflow-issue-start/SKILL.md
      issueflow-issue-pause/SKILL.md
      issueflow-issue-close/SKILL.md
      issueflow-issue-cleanup/SKILL.md
      issueflow-issue-yolo/SKILL.md
      issueflow-issue-fix/SKILL.md
      issueflow-version-bump/SKILL.md
      issueflow-history-update/SKILL.md
      issueflow-graphify/SKILL.md
    rules/
      issueflow-rules.mdc    # Always-on Cursor rule for the workflow
  AGENTS.md                  # Workflow rules (managed block; shared by all editors)
  docs/
    issue-workflow.md        # Human-readable overview of the workflow
```

The exact `agent_dir` and the per-editor rules file depend on which editor(s) you scaffold for — see [Editor support](#editor-support). `AGENTS.md` (written as a non-destructive managed block) and `docs/issue-workflow.md` are shared by every editor.

The Cursor slash commands give agents a repeatable flow. The linear path is:

1. `/issue-init 42` — pulls GitHub issue #42 into `.issueflows/01-current-issues/` and archives older issues.
2. `/issue-plan` — drafts `issue<N>_plan.md` (Goal / Constraints / Approach / Files to touch / Test strategy / Open questions) and stops for your confirmation.
3. `/issue-start` — reads the confirmed plan and implements it. If no plan file exists, it offers to run `/issue-plan` first, proceed without a plan, or abort.
4. `/issue-close` — runs tests, optionally bumps version with `uv version --bump`, appends a `HISTORY.md` entry (or promotes `[Unreleased]` to a new release section on a bump), updates status files, commits, pushes, and opens a PR.
5. `/issue-cleanup` — after the PR merges, switches to the default branch, fast-forwards, prunes, and deletes the merged local branch.

Plus a few off-path commands:

- `/issue-pick` — **front door**: when you haven't chosen an issue yet, it helps pick one (parked work in `02-partly-solved-issues/` first, else open GitHub issues ranked by milestone, labels, and similarity to recently solved work), creates the `<N>-slug` branch, and runs `/issue-init`. Pass `fix` to create a new general-fixes issue. Off-path; never auto-dispatched.
- `/iflow` — **quick start**: inspects the current issue's state and dispatches to the right linear step automatically. A branch-derived number (`42-fix-login` → `N=42`) is authoritative, so `/iflow` works from a fresh branch too.
- `/issue-pause` — park the current issue in `02-partly-solved-issues/` with a **Remaining work** note; optional WIP commit + switch back to the default branch.
- `/issue-yolo` — all-in-one chain (`init → plan → start → close`) for small, low-risk issues, with up-front safeguards (refuses on the default branch, refuses with dirty unrelated changes, requires passing tests, single consolidated confirm).
- `/issue-fix` — interactive iterative-fixes session: creates one GitHub issue + long-lived branch, then loops over many small fixes (each gets a short plan, implemented only on confirmation and recorded in `issue<N>_status.md`), ending with `/issue-close`. Coexists with `/issue-pick fix` (the one-shot setup). Off-path; never auto-dispatched.

The matching **Agent Skills** (under `.cursor/skills/`) carry the same workflows for on-demand use with `/issueflow-issue-pick`, `/issueflow-iflow`, `/issueflow-issue-init`, `/issueflow-issue-plan`, `/issueflow-issue-start`, `/issueflow-issue-pause`, `/issueflow-issue-close`, `/issueflow-issue-cleanup`, `/issueflow-issue-yolo`, `/issueflow-issue-fix`, `@issueflow-version-bump` when you need only the bump steps, or `@issueflow-history-update` when you need only the changelog update (see [Cursor Agent Skills](https://cursor.com/docs/context/skills)).

## Prerequisites

issue-flow itself is a small Python CLI, but the **scaffolded slash commands
it writes into your project shell out to a few external tools**. If they are
missing, the slash commands will fail at runtime — so `issue-flow init` now
checks for them up front and prints install hints before it does anything.

Required:

- **[Git](https://git-scm.com/downloads)** — used by every slash command for
branch, fetch, status, commit, and push operations. Almost certainly already
installed if you're here, but the check covers it for completeness.
- **[GitHub CLI (`gh`)](https://cli.github.com/)** — used by `/issue-init` to
fetch issues, by `/issue-close` to open PRs, and by `/issue-cleanup` to check
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
- A new slash command `/graphify` (and matching `/issueflow-graphify` skill) wraps
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
- The scaffolded rules and `/issue-start` mention `graphify-out/GRAPH_REPORT.md`
as a recommended pre-read when the file exists. `/graphify` is **off-path** —
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
> venv but leaves the `graphify` CLI invisible to the shell, so `/graphify`
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

That's it. Open the project in Cursor and start with `/iflow` (or step through `/issue-init`, `/issue-plan`, `/issue-start`, `/issue-close`, `/issue-cleanup` explicitly).

## Usage

```
issue-flow init [PROJECT_DIR] [--force] [--skip-dep-check]
issue-flow update [PROJECT_DIR] [--skip-dep-check]
issue-flow graphify [-C PROJECT_DIR] [...graphify subcommand + args]
```

### `issue-flow init`


| Argument / Option  | Description                                                                                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROJECT_DIR`      | Project root directory. Defaults to `.` (current directory).                                                                                                               |
| `--force`, `-f`    | Overwrite generated commands, rules, and workflow doc instead of skipping them.                                                                                            |
| `--skip-dep-check` | Skip the external-CLI dependency check (`git`, `gh`) and the confirmation prompt that follows if anything is missing. Useful in automation.                                |
| `--editor`, `-e`   | AI coding tool(s) to scaffold for: `cursor` (default), `claude`, `opencode`, `codex`, or `all`. Repeatable (`-e cursor -e claude`). See [Editor support](#editor-support). |


Running `init` again without `--force` is safe: generated scaffold files that already exist are skipped, and **issue markdown under `.issueflows/` is never touched** by `init` or `update`. When the CLI detects an existing scaffold, it reminds you about `update` and `--force`.

### `issue-flow update`


| Argument / Option  | Description                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PROJECT_DIR`      | Project root directory. Defaults to `.` (current directory).                                                                                      |
| `--skip-dep-check` | Skip the external-CLI dependency check (`git`, `gh`) and the confirmation prompt that follows if anything is missing.                             |
| `--editor`, `-e`   | AI coding tool(s) to refresh for: `cursor` (default), `claude`, `opencode`, `codex`, or `all`. Repeatable. See [Editor support](#editor-support). |


Use `update` after upgrading the **issue-flow** package to refresh the packaged slash commands, rules file(s), and `docs/issue-workflow.md` from the version you have installed. This **overwrites** those generated files (unlike a plain second `init`). It still does not modify arbitrary files under `.issueflows/` (for example your `issue*_original.md` / `issue*_status.md` files), and it creates any **new** `.issueflows/` subdirectories required by the current package.

### `issue-flow graphify`


| Argument / Option               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `-C`, `--project-dir`           | Project root directory to scan with graphify. Defaults to `.` (current directory). Modeled on `git -C` so positional args can flow into graphify untouched.                                                                                                                                                                                                                                                                                                                                                                                                              |
| `...graphify subcommand + args` | Optional graphify subcommand + flags. With no extras runs `graphify update <PROJECT_DIR>` — AST-only, **no LLM API key required**. The first extra arg, if it is a recognized build subcommand (`update`, `extract`, `watch`, `cluster-only`, `check-update`), picks the action; trailing tokens forward verbatim. Examples: `issue-flow graphify extract` (semantic LLM pass; needs `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `MOONSHOT_API_KEY` or `--backend ollama`), `issue-flow graphify cluster-only --no-viz`, `issue-flow graphify ./subdir`. |


`graphify` requires `graphifyy` to be installed (`uv tool install graphifyy`). When the `graphify` CLI is missing, the command prints install hints and exits with code `2`. Outputs land in `graphify-out/` (`graph.html`, `GRAPH_REPORT.md`, `graph.json`).

### When to use which


| Goal                                                                 | Command                   |
| -------------------------------------------------------------------- | ------------------------- |
| First-time setup, or add missing files only                          | `issue-flow init`         |
| Pull newer templates after `uv tool upgrade issue-flow` (or similar) | `issue-flow update`       |
| Replace generated scaffolds without upgrading logic                  | `issue-flow init --force` |
| Rebuild the graphify knowledge graph                                 | `issue-flow graphify`     |


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
every editor gets the full set. `**AGENTS.md`** is the convergent rules file and
is written for every editor as a non-destructive *managed block* (issue-flow
only ever owns the content between its markers, so a hand-maintained `AGENTS.md`
is preserved). Slash commands and an editor-specific rules file are layered on
top where the tool supports them.


| Editor      | `agent_dir`  | Slash commands | Skills | Extra rules file                    | `AGENTS.md` | graphify auto-register |
| ----------- | ------------ | -------------- | ------ | ----------------------------------- | ----------- | ---------------------- |
| Cursor      | `.cursor/`   | `commands/`    | yes    | `.cursor/rules/issueflow-rules.mdc` | yes         | yes                    |
| Claude Code | `.claude/`   | `commands/`    | yes    | `CLAUDE.md`                         | yes         | no                     |
| opencode    | `.opencode/` | `command/`     | yes    | —                                   | yes         | no                     |
| Codex       | `.codex/`    | — (use skills) | yes    | —                                   | yes         | no                     |


Codex CLI removed project-scoped slash commands, so on Codex you invoke the
mirrored skills (e.g. `issueflow-issue-init`) instead of `/issue-init`. The
graphify integration currently registers only with Cursor; other editors still
get the `/graphify` command/skill but no automatic `graphify cursor install`.

## Configuration

issue-flow reads a `.env` file from the project root (.via python-dotenv). The following environment variables are supported:


| Variable                 | Default        | Description                                                                                                                                   |
| ------------------------ | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `ISSUEFLOW_DIR`          | `.issueflows`  | Name of the issue-tracking directory.                                                                                                         |
| `ISSUEFLOW_EDITOR`       | `cursor`       | Default editor profile when `--editor` is not passed (`cursor`, `claude`, `opencode`, `codex`).                                               |
| `ISSUEFLOW_AGENT_DIR`    | *(per editor)* | Override the agent/IDE config directory. When unset it is derived from the editor profile (e.g. `.cursor`, `.claude`, `.opencode`, `.codex`). |
| `ISSUEFLOW_DOCS_DIR`     | `docs`         | Where to write the workflow documentation file.                                                                                               |
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md`   | Changelog file that `/issue-close` updates (set to e.g. `CHANGELOG.md` for different conventions).                                            |

Beyond the `ISSUEFLOW_*` settings above, `issue-flow graphify` also reads an LLM
API key from `.env` when present (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, or `MOONSHOT_API_KEY`) and passes it through to the
`graphify extract` semantic pass. The no-arg `graphify update` build is
AST-only and needs no key.


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
- `**issue-flow status`** — show a dashboard of current, partly-solved, and solved issues.
- **Custom templates** — let users supply their own Jinja2 templates to tailor slash commands and rules to their team's conventions.
- **Git hook integration** — optionally move issue files on commit based on status markers.
- **GitHub Actions workflow** — ship a reusable action that syncs issue state between `.issueflows/` and GitHub issue labels/milestones.

## License

This project is released under the MIT License. See the full text in the repository: [LICENSE](https://github.com/jepegit/issue-flow/blob/main/LICENSE).