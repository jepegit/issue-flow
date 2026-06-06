# Issue #56 plan — rename `build` → `graphify`

## Goal

Rename the graph-rebuild surface from `build` to `graphify` so the slash command is `/graphify`, the skill is `issueflow-graphify`, and the CLI subcommand is `issue-flow graphify`. No behavior change — pure rename + doc refresh.

## Decisions

- Slash command/file: `/build` → `/graphify` (`commands/build.md(.j2)` → `commands/graphify.md(.j2)`).
- Skill: `issueflow-build` → `issueflow-graphify` (template dir `issueflow_build` → `issueflow_graphify`; generated dir `issueflow-build` → `issueflow-graphify`; `name:` frontmatter).
- CLI: Typer command function `build` → `graphify` (so `issue-flow build` → `issue-flow graphify`).
- Internal `run_build`/`_build_graphify_argv`/`_GRAPHIFY_BUILD_SUBCOMMANDS`/`_DEFAULT_BUILD_SUBCOMMAND` are kept — they describe graphify's *build-the-graph* operation, are not user-facing, and renaming them adds churn/risk with no user benefit. Only docstrings/comments that name the user-facing `/build` or `issue-flow build` are updated.

### Prior art

- `.issueflows/04-designs-and-guides/graphify-integration.md` — the graphify integration design doc (#49). Will append a short rename note there.
- None found beyond the graphify integration itself (grep + manifest checked).

## Files to touch

Source:
- `src/issue_flow/cli.py` — rename `build` Typer command → `graphify`; refresh docstring.
- `src/issue_flow/graphify.py` — refresh docstrings/comments that name `/build` / `issue-flow build`.
- `src/issue_flow/dependencies.py` — Graphify `purpose` mentions `/build`.
- `src/issue_flow/templating.py` — manifest entries for command + skill paths.

Templates:
- Rename `templates/commands/build.md.j2` → `graphify.md.j2` (+ content).
- Rename `templates/skills/issueflow_build/SKILL.md.j2` → `issueflow_graphify/SKILL.md.j2` (+ content).
- `templates/commands/iflow.md.j2`, `issue-start.md.j2`, `issue-close.md.j2`, `rules/issueflow-rules.mdc.j2`, `docs/cursor-issue-workflow.md.j2` — cross-refs.

Repo's own generated dogfood copies + docs:
- Rename `.cursor/commands/build.md` → `graphify.md`; `.cursor/skills/issueflow-build/` → `issueflow-graphify/`.
- `.cursor/commands/iflow.md`, `issue-start.md`, `issue-close.md`, `.cursor/rules/issueflow-rules.mdc`, `docs/cursor-issue-workflow.md`, `README.md` — cross-refs.

Tests:
- `tests/test_cli.py`, `tests/test_templating.py`, `tests/test_init.py` — update `build` → `graphify` expectations. (`test_graphify.py`, `test_dependencies.py` unaffected — they use the unchanged internal API / `graphify` command name.)

Design doc:
- `.issueflows/04-designs-and-guides/graphify-integration.md` — append rename note.

## Test strategy

`uv run pytest` — all 106 tests must pass after the rename (several assert on `build`/`issueflow-build` strings and will be updated to `graphify`).
