# Developing issue-flow

A step-by-step guide for working on the issue-flow codebase. You don't need to be a Python expert to contribute -- just follow along.

---

## Prerequisites

You'll need these installed on your machine:

- **Python 3.13+** -- check with `python --version`
- **uv** -- our project tool ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **git** -- for version control
- **gh** -- the GitHub CLI ([install guide](https://cli.github.com/)), used for creating releases

---

## Getting started

Clone the repo and install everything:

```bash
git clone https://github.com/jepegit/issue-flow.git
cd issue-flow
uv sync
```

`uv sync` reads `pyproject.toml`, creates a virtual environment in `.venv/`, and installs all dependencies (including dev tools like pytest and ruff). You don't need to activate the virtual environment -- `uv run` handles that for you.

---

## Day-to-day commands

Here are the commands you'll use most often:

| What | Command |
|------|---------|
| Run tests | `uv run pytest` |
| Run tests (verbose) | `uv run pytest -v` |
| Lint the code | `uv run ruff check src/ tests/ scripts/` |
| Auto-fix lint issues | `uv run ruff check --fix src/ tests/ scripts/ scripts/` |
| Format the code | `uv run ruff format src/ tests/ scripts/` |
| Add a dependency | `uv add <package>` |
| Add a dev dependency | `uv add --dev <package>` |
| Run the CLI locally | `uv run issue-flow --help` |
| Refresh scaffold in a test project (same as installed package templates) | `uv run issue-flow update <DIR>` |
| Refresh **this** repo's `.cursor/` and generated workflow doc from templates | `uv run scripts/update_issueflow_setup.py` |

Always use `uv run` instead of calling `python` directly. This makes sure you're using the right virtual environment and dependencies.

---

## Project structure

```text
issue-flow/
  scripts/                # Maintainer helpers (e.g. refresh local Cursor scaffold)
  src/issue_flow/         # The actual package
    __init__.py           # Version string
    cli.py                # Command-line interface (typer)
    config.py             # Settings loaded from .env / environment
    editors.py            # Per-editor scaffolding profiles (cursor, claude, ...)
    modes.py              # Scaffolding-mode registry, resolution, persistence
    modes.toml            # Built-in mode definitions (standard, simple)
    init.py               # `init` and `update` command logic
    templating.py         # Jinja2 template loading
    templates/            # Templates rendered by "init"
      commands/           # Cursor slash command templates
      rules/              # Cursor rule templates
      skills/             # Cursor Agent Skill templates (SKILL.md per skill)
      docs/               # Documentation templates
  tests/                  # Test files
  docs/                   # Documentation (you are here)
  .github/workflows/      # CI and publishing automation
  .issueflows/            # Yes, we are also using issue-flow
      00-tools/                 # Helper scripts and utilities
      01-current-issues/        # Active issues being worked on
      02-partly-solved-issues/  # Issues with partial progress
      03-solved-issues/         # Completed issues
      04-designs-and-guides/    # Durable design docs and project brief
      05-epics/                 # Staged epic plans (epic<N>_plan.md)
```

---

## Working on scaffolding modes

End-user docs for what a mode is, how to pick one, and custom project modes live
in [Configuration → Modes](configuration.md#modes). This section is for
contributors changing how modes work in the package.

**Built-in mode definitions** ship in
[src/issue_flow/modes.toml](../src/issue_flow/modes.toml). Each `[modes.<id>]`
table accepts `name`, `description`, `skills`/`commands` (`"all"` or a list of
stems), or `extends` + `add`/`remove` to compose on top of another mode.
**Resolution and persistence** live in
[src/issue_flow/modes.py](../src/issue_flow/modes.py).

Templates branch on surface membership via `included_skills` /
`included_commands` (not on the mode id), so new modes and surfaces compose
without per-mode conditionals. When you add a skill or command, gate it in
templates the same way.

**Smoke test:** `uv run issue-flow init /tmp/test-project --mode simple`

**Tests:** `uv run pytest tests/test_modes.py` (plus `test_init.py` /
`test_update.py` if manifest filtering changes).

---

## Running tests

```bash
uv run pytest
```

That's it. Tests live in the `tests/` folder. If you add a new feature, add a test for it in the matching `test_*.py` file.

To run a single test file:

```bash
uv run pytest tests/test_init.py
```

To run a single test by name:

```bash
uv run pytest -k "test_init_creates_directories"
```

---

## Linting

We use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting. Before you commit, run:

```bash
uv run ruff check src/ tests/ scripts/
```

If ruff reports issues it can fix automatically:

```bash
uv run ruff check --fix src/ tests/ scripts/
```

---

## How CI works

We have two GitHub Actions workflows:

**CI** (`.github/workflows/ci.yml`) -- runs on every push and pull request to `main`:
- Installs dependencies
- Runs ruff
- Runs pytest

**Publish** (`.github/workflows/publish.yml`) -- runs when you create a GitHub release:
- Runs the full test suite first
- Builds the package
- Publishes to PyPI using Trusted Publishing (no API tokens needed)

---

## Publishing a new version

`issue-flow` uses a **static** version in `pyproject.toml` (see the
"Release & version bump" section of
`.issueflows/04-designs-and-guides/this-project.md`). Prefer shipping a
dedicated release issue (e.g. `/iflow-pick` → plan → build →
`/iflow-close`) so HISTORY, docs, and the bump land in one PR — then tag
on `main` after merge.

### 1. Make sure tests pass

```bash
uv run pytest -v
uv run ruff check src/ tests/
```

Don't skip this. If tests fail, the publish workflow will also fail.

### 2. Bump the version and promote HISTORY

Preview, then write:

```bash
uv version --dry-run --bump patch --short   # e.g. 0.4.8 -> 0.4.9
uv version --bump patch                     # or: minor / major / alpha / …
```

`uv version --bump <level>` updates `[project].version` in `pyproject.toml`.
Levels follow [PEP 440](https://packaging.python.org/en/latest/specifications/pep-0440/)
via uv (`patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`,
`dev`). A bare `bump` in `/iflow-close` stays on the current pre-release
channel when the version is already an alpha/beta/rc.

Also promote `HISTORY.md`: rename `## [Unreleased]` to
`## [<new_version>] - YYYY-MM-DD`, move the release bullets into that
section, and open a fresh empty `## [Unreleased]` above it. `/iflow-close`
with a bump token does this via the `iflow-history-update` skill; if you
bump by hand, edit `HISTORY.md` the same way. Drop any Unreleased bullet
that already shipped in an earlier tag.

### 3. Commit, push, and merge the release PR

```bash
git add pyproject.toml HISTORY.md docs/
# include uv.lock only if it changed
git commit -m "Release 0.4.9"
git push
```

Open/merge a PR into `main` (squash). Do **not** create the GitHub release
tag on the issue branch — under squash merges that commit never lands on
`main`.

### 4. Create a GitHub release (on updated `main`)

After the bump PR is merged and local `main` is fast-forwarded:

```bash
git switch main && git pull --ff-only
gh release create "v$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")" --generate-notes
```

Or, if you keep a local `release` alias (see below), just run `release`.
Creating the GitHub release starts `.github/workflows/publish.yml`, which
re-runs tests, builds the package, and publishes to PyPI.

### The `release` alias

Optional convenience in a gitignored `.aliases` file:

```bash
alias release='gh release create "v$(python -c "import tomllib; print(tomllib.load(open(\"pyproject.toml\",\"rb\"))[\"project\"][\"version\"])")" --generate-notes'
```

This alias:
1. Reads the current version from `pyproject.toml`
2. Prefixes it with `v` (e.g. `0.4.9` becomes `v0.4.9`)
3. Creates a GitHub release with that tag
4. Auto-generates release notes from merged PRs and commits

If your shell is set up to source `.aliases` when entering a directory, this works automatically. Otherwise, run `source .aliases` once per terminal session.

---

## Trusted Publishing (one-time setup)

The publish workflow uses PyPI Trusted Publishing, which means no API tokens are stored in GitHub secrets. If this isn't set up yet for a new PyPI project:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a pending publisher:
   - **Owner**: `jepegit`
   - **Repository**: `issue-flow`
   - **Workflow name**: `publish.yml`
   - **Environment**: `pypi`
3. In GitHub repo settings, go to Settings > Environments > New environment, name it `pypi`.

You only need to do this once.

---

## Quick reference

```bash
# Set up
uv sync

# Develop
uv run pytest
uv run ruff check src/ tests/ scripts/
uv run scripts/update_issueflow_setup.py
uv run issue-flow init /tmp/test-project

# Release (after merge to main)
uv version --bump patch
# promote HISTORY.md [Unreleased] → ## [x.y.z] - YYYY-MM-DD
git add pyproject.toml HISTORY.md && git commit -m "Release x.y.z" && git push
# after PR merges:
gh release create "v$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")" --generate-notes
```
