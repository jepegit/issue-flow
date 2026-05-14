# Status for issue #49: add graphify

- [x] Done

## What landed

- **No Python dependency on graphify** (revised after initial draft — see "Plan deviations" below). graphify is treated as an external CLI, the same way `git` and `gh` are; users install it standalone via `uv tool install graphifyy`.
- **`src/issue_flow/graphify.py`** — `is_available`, `register_with_cursor` (best-effort `graphify cursor install`), and `run_build` (subprocess passthrough). Never raises; falls back to install hints when graphify is absent.
- **`src/issue_flow/dependencies.py`** — added `RECOMMENDED_DEPENDENCIES` (non-blocking) with the graphify entry and a `check_recommended` helper.
- **`src/issue_flow/init.py`** — `_graphify_postinstall` runs at the end of `run_init` and `run_update`, delegating to `register_with_cursor`. No flag plumbing.
- **`src/issue_flow/cli.py`** — new `build` Typer command with `allow_extra_args=True` so `issue-flow build [PROJECT_DIR] [--update --no-viz --mode deep ...]` forwards every flag verbatim to `graphify`. Exits `2` when graphify is missing, propagates graphify's exit code otherwise.
- **`src/issue_flow/templating.py`** — new manifest entries for `commands/build.md.j2` and `skills/issueflow_build/SKILL.md.j2` (manifest count: 21 → 23).
- **New scaffold templates** — `templates/commands/build.md.j2` and `templates/skills/issueflow_build/SKILL.md.j2`.
- **Edits to existing scaffold templates**:
  - `iflow.md.j2` — lists `/build` as off-path; adds a graphify-stale hint.
  - `issue-start.md.j2` — adds an optional "Knowledge graph" pre-read step pointing at `graphify-out/GRAPH_REPORT.md`.
  - `issue-close.md.j2` — adds an optional "Graph freshness" suggestion in the sanity-check step.
  - `issueflow-rules.mdc.j2` — new "Knowledge graph (optional, via graphify)" section.
  - `cursor-issue-workflow.md.j2` — table updated, new section 7 for `/build`, skill table updated.
- **PATH-orphan detection** (added late) — `find_orphan_install()` probes well-known install dirs (`~/.local/bin`, plus a couple of Windows-specific Scripts dirs). When graphify is missing from PATH but found at a candidate location, the missing-CLI hint switches to a "found but not on PATH" message that names the directory and suggests `uv tool update-shell` plus a shell/Cursor restart. The plain "missing" branch also got an "already installed?" tail so users who just ran `uv tool install graphifyy` don't get confused. README has matching guidance.
- **Tests** — full suite green (100 passing). New files:
  - `tests/test_graphify.py` — detection, register_with_cursor success/failure paths, run_build passthrough and missing-CLI handling, PATH-orphan detection (5 new tests).
  - `tests/test_cli.py` — Typer CLI smoke tests for `build`.
  - Extended `tests/test_init.py` (graphify register wiring, build template scaffold check, knowledge-graph rule section).
  - Extended `tests/test_dependencies.py` (recommended graphify entry, `check_recommended`).
  - Updated `tests/test_templating.py` manifest count and expected commands/skills.
- **Docs** — `readme.md` gains a "Optional: graphify integration" section, the directory listing, and an `issue-flow build` entry; `.issueflows/04-designs-and-guides/graphify-integration.md` captures the decisions.

## Verified

- `uv run pytest` — 95 passed.
- `uv run ruff check src/ tests/` — clean.

## Plan deviations

- **Dropped the `[project.optional-dependencies] graphify` extra** mid-implementation. Reason: `uv tool install <pkg>` only puts the host package's entry-point scripts on PATH, so `uv tool install 'issue-flow[graphify]'` would install graphifyy into issue-flow's venv but leave the `graphify` CLI invisible to the shell — the extra advertised something it could not deliver to the primary install audience. The integration now treats graphify like `git` / `gh`: an external CLI installed separately. README, `dependencies.py` install hints, and the design doc were all updated to match.
- The plan mentioned "or extend `format_missing_report`" — chose the dedicated `RECOMMENDED_DEPENDENCIES` list + `check_recommended` helper instead. Cleaner separation: required deps still block via `format_missing_report`; recommended deps only inform.
- `run_build` uses a narrow heuristic for path injection: if `extra_args` is empty *or* its first token starts with `-`, we inject the project root; otherwise we trust the user's positional. This handles `--mode deep` (where `deep` is a flag value, not a path) correctly.
- Did not add a `tests/__init__.py` for the new `templates/skills/issueflow_build/` folder (matches the existing skills, which also have none).
