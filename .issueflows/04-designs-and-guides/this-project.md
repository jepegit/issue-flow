# issue-flow

## What this project is

**issue-flow** is a small Python CLI that scaffolds a lightweight,
agent-friendly issue-tracking workflow into *other* projects. Running
`issue-flow init` writes a `.issueflows/` tracking tree plus editor skills,
rules, and slash-command files so AI agents can pick up GitHub issues, plan
work, and land PRs in a consistent way. **This repo *is* the tool** — not a
project scaffolded by it (though it dogfoods its own workflow).

## Stack / runtime

- **Language/runtime:** Python **3.13+** (pinned in `.python-version`).
- **Package manager:** **`uv`** exclusively (uv-managed `.venv`). Never `pip`,
  `pip-tools`, or `poetry`.
- **Build backend:** `uv_build`. Entry point: `issue-flow = "issue_flow.cli:main"`.
- **Runtime deps:** `jinja2`, `python-dotenv`, `rich`, `tomlkit`, `typer`
  (declared in `pyproject.toml`; `tomlkit` round-trips `config.toml` preserving
  comments, stdlib `tomllib` is read-only). Dev group: `pytest`, `ruff`.
- **External CLIs agents should know about:** `git` and `gh` (required for the
  issue workflow), plus optional `graphify` (knowledge-graph integration,
  installed as its own `uv` tool).

## How to run / test

```bash
uv sync                          # install/refresh deps from the lock file
uv run pytest                    # run the test suite
uv run ruff check src/ tests/    # lint
uv version --bump <part>         # bump version (used by /iflow-close)
```

Exercise the CLI end-to-end by scaffolding a throwaway project: `git init` an
empty dir, then `uv run --project <repo> issue-flow init . --skip-dep-check`
(`--skip-dep-check` avoids the interactive git/gh prompt in headless runs).

### Editable `uv tool` install — dependency refresh gotcha

When developing, you typically install issue-flow as a **local editable `uv`
tool** so the `issue-flow` binary on `PATH` runs your live source:

```bash
uv tool install --force --editable .
```

Key behaviour:

- The editable link means **code edits apply instantly** — no reinstall needed.
- But the tool's isolated venv only contains the dependencies resolved **at
  install time**. If you **add / remove / bump a dependency** in
  `pyproject.toml`, the linked code sees the change but the venv does **not** →
  you get `ModuleNotFoundError` (this is exactly what caused issue #94:
  `No module named 'tomlkit'` from a venv resolved before `tomlkit` was added).
- **Fix:** rerun `uv tool install --force --editable .` to rebuild the venv and
  re-resolve deps. `uv tool upgrade issue-flow` alone does **not** reliably
  re-resolve a local editable install.
- Do **not** confuse this with the `issue-flow update` *subcommand* — that
  re-scaffolds `.issueflows/`/skills into a target project and touches nothing
  in the tool's venv.

> Rule of thumb: edit code → no action. Change a dependency → rerun
> `uv tool install --force --editable .`.

## Conventions

- **Templates are the source of truth.** Files generated into target projects
  (slash commands, skills, the always-on rule) come from
  `src/issue_flow/templates/`. When changing scaffold behaviour, edit the
  **templates**, not any already-rendered copy.
- **Branches:** do issue work on an issue branch named `<N>-<short-slug>`, not
  the default branch. PRs are assumed **squash-merged**; run `/iflow-cleanup`
  after merge.
- **Commits:** only commit when explicitly asked.
- **Issue workflow:** this repo follows the issue-flow lifecycle it ships —
  `/iflow-init` → `/iflow-plan` → `/iflow-start` → `/iflow-close` →
  `/iflow-cleanup` (with `/iflow` as the smart dispatcher, `/iflow-pick` /
  `/iflow-pause` / `/iflow-yolo` off-path). Keep status files accurate with an
  explicit `- [x] Done` / `- [ ] Done` checkbox.
- **Config:** reads a `.env` from the project root (`ISSUEFLOW_DIR`,
  `ISSUEFLOW_AGENT_DIR`, `ISSUEFLOW_DOCS_DIR`, `ISSUEFLOW_HISTORY_FILE`).
  Project-level toggles live in `.issueflows/config.toml` under `[issueflow]`
  (e.g. `mode`, `caveman_default`, `grill_me_default`).

## Release & version bump

- **Static version (uv):** `[project] version` lives in `pyproject.toml`;
  bump with `uv version --bump <level>` before the release commit (the
  `/iflow-close` default). Versions are PEP 440 with alpha pre-releases
  (`0.4.2a3`); a bare `bump` stays on the current pre-release channel.
- Publishing to PyPI runs from `.github/workflows/publish.yml`.

## Entry points

- **CLI:** `src/issue_flow/cli.py` (Typer) — `init` / `update` / `graphify`
  plus agent-facing subcommands (`agent capture` / `sweep` / `preflight` /
  `status` / `state`).
- **Scaffolding logic:** `src/issue_flow/init.py` (writes `.issueflows/` +
  editor config).
- **Other core modules:** `config.py` (env/config), `modes.py` (scaffolding
  modes), `editors.py` (editor profiles), `templating.py` (Jinja2 helpers),
  `dependencies.py` (git/gh/graphify checks), `gitutils.py`, `agent.py`,
  `graphify.py`.
- **Templates:** `src/issue_flow/templates/` (`commands/`, `skills/`, `rules/`).
- **Tests:** `tests/` (pytest). **Read first:** `AGENTS.md`, this file, then the
  module matching the area you're changing.

## Non-goals / known limitations

- Not a full issue tracker or GitHub replacement — it scaffolds a
  **file-based**, agent-friendly workflow around existing GitHub issues.
- Targets the **Cursor** editor surface primarily (skills/rules/commands);
  other editors are partially supported via editor profiles.
- The `graphify` knowledge-graph integration is **optional** and off-path
  (never auto-run); ignore graph guidance when `graphify-out/` is absent.
- Requires Python **3.13+**; no support for older interpreters.
