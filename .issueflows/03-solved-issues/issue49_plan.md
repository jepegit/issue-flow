# Plan for issue #49: add graphify

## Goal

Wire [graphify](https://graphify.net) (PyPI: `graphifyy`, CLI: `graphify`) into issue-flow so that scaffolded projects automatically register the graphify Cursor skill, ship a new `issue-flow build` command (and `/build` slash command) that rebuilds the knowledge graph, and the existing rules / commands tell agents to consult `graphify-out/GRAPH_REPORT.md` when it exists.

## Decisions confirmed with user

- **Dependency model:** optional Python extra. `pyproject.toml` gains `[project.optional-dependencies] graphify = ["graphifyy>=0.7"]`. issue-flow always shells out to the `graphify` CLI; the extra just guarantees it gets installed.
- **Activation:** auto-detect, no `--with graphify` flag. If `graphify` is on `PATH` at init/update time we wire it in; otherwise we print a one-line hint. Graphify-aware lines in the scaffolded markdown are always rendered (they no-op when the graph isn't built).
- **Lifecycle depth:** medium. New `/build` slash command, `graphify cursor install` is auto-run from `init`/`update`, and `issueflow-rules.mdc` + `/issue-start` + `/issue-close` get short graphify-aware additions. No automatic `graphify .` rebuilds from `/issue-close` and no `graphify hook install`.

## Constraints

- Project rules (`uv` only, `uv add` / `uv sync`, `uv run`).
- Back-compat: existing `init` / `update` flows must keep working unchanged when `graphify` is not installed (no errors, just a hint). `update` must still leave `.issueflows/` issue files untouched.
- Don't add `graphifyy` as a hard dependency — it pulls a large transitive footprint.
- `graphify cursor install` must be best-effort: if it fails, we report and continue (don't fail `init`).

## Approach

1. **`graphify` helper module** — new `src/issue_flow/graphify.py` with `is_available`, `register_with_cursor` (best-effort `graphify cursor install`), and `run_build` (subprocess passthrough).
2. **Wire into `init` / `update`** — call a new `_graphify_postinstall(project_root)` near the end of `run_init` / `run_update`.
3. **Add `build` CLI command** — Typer command with extra-args passthrough so `issue-flow build --update`, `--no-viz`, etc. forward verbatim.
4. **New scaffolded `/build` slash command** + matching agent skill, registered in `TEMPLATE_MANIFEST`.
5. **Light edits to existing scaffold templates** — rules, `/iflow`, `/issue-start`, `/issue-close`, workflow doc.
6. **Recommended (non-blocking) dependency hint** for `graphify` in `dependencies.py`.
7. **Design decision record** under `.issueflows/04-designs-and-guides/`.

## Files to touch

- `pyproject.toml` — `[project.optional-dependencies] graphify = ["graphifyy>=0.7"]`.
- `src/issue_flow/cli.py` — `build` Typer command.
- `src/issue_flow/init.py` — `_graphify_postinstall` wiring.
- `src/issue_flow/graphify.py` — new module.
- `src/issue_flow/dependencies.py` — non-blocking recommended dep hint.
- `src/issue_flow/templating.py` — manifest entries for `build.md.j2` and `skills/issueflow_build/SKILL.md.j2`.
- `src/issue_flow/templates/commands/build.md.j2` — new `/build` slash command.
- `src/issue_flow/templates/commands/iflow.md.j2` — list `/build` as off-path.
- `src/issue_flow/templates/commands/issue-start.md.j2` — graphify reading hint.
- `src/issue_flow/templates/commands/issue-close.md.j2` — graphify rebuild hint.
- `src/issue_flow/templates/rules/issueflow-rules.mdc.j2` — "Knowledge graph" section.
- `src/issue_flow/templates/docs/cursor-issue-workflow.md.j2` — paragraph on graphify integration.
- `src/issue_flow/templates/skills/issueflow_build/SKILL.md.j2` — new matching skill.
- `readme.md` — integration docs, `[graphify]` extra, `build` command.
- `.issueflows/04-designs-and-guides/graphify-integration.md` — new decision record.

## Test strategy

- Re-run existing: `uv run pytest`, `uv run ruff check src/ tests/`.
- New tests:
  - `tests/test_graphify.py` — `is_available`, `register_with_cursor` (success + failure), `run_build` (exit code + missing-CLI error).
  - `tests/test_init.py` — extend with mocked `graphify.is_available()` branches.
  - `tests/test_templating.py` — manifest renders new templates cleanly.
  - `tests/test_cli.py` — `issue-flow build` exits 0/1 with mocked subprocess and forwards extra args.

## Open questions

- Build skill name `issueflow-build` (chosen for parity).
- Pure passthrough for `build` flags in v1.
