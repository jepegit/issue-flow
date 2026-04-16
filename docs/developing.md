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
```

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

Here's the full process, step by step.

### 1. Make sure tests pass

```bash
uv run pytest -v
uv run ruff check src/ tests/ scripts/
```

Don't skip this. If tests fail, the publish workflow will also fail.

### 2. Bump the version

```bash
uv version 0.2.0
```

This updates the version in `pyproject.toml`. Pick a version number following [semantic versioning](https://semver.org/):
- **Patch** (0.1.0 -> 0.1.1): bug fixes
- **Minor** (0.1.0 -> 0.2.0): new features, backwards compatible
- **Major** (0.1.0 -> 1.0.0): breaking changes

### 3. Commit and push

```bash
git add pyproject.toml uv.lock
git commit -m "Bump version to 0.2.0"
git push
```

### 4. Create a release

If you have the `.aliases` file sourced in your shell (see below), just run:

```bash
release
```

This reads the version from `pyproject.toml` and creates a GitHub release with auto-generated notes. The publish workflow kicks in automatically.

If you don't have the alias, the full command is:

```bash
gh release create v0.2.0 --generate-notes
```

### The `release` alias

The original developer typically have a `.aliases` file that is automatically read containing a handy shortcut:

```bash
alias release='gh release create "v$(python -c "import tomllib; print(tomllib.load(open(\"pyproject.toml\",\"rb\"))[\"project\"][\"version\"])")" --generate-notes'
```

Note that the `.aliases` file is ignored by git (it is included in `.gitignore`). So if you want to adopt the `.aliases` way of doing things, you need to make it yourself (i.e., creating a file called `.aliases` and copy-pasting the alias command above inside it).

This alias:
1. Reads the current version from `pyproject.toml`
2. Prefixes it with `v` (e.g. `0.2.0` becomes `v0.2.0`)
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

# Release
uv version 0.2.0
git add pyproject.toml uv.lock && git commit -m "Bump version to 0.2.0" && git push
release
```
