# Issue #56 status — rename `build` → `graphify`

- [x] Done

## What was done

Renamed the graph-rebuild surface from `build` to `graphify` throughout the package and its scaffolded output. No behavior change — pure rename + doc refresh.

### Source
- `cli.py` — Typer command `build` → `graphify` (CLI subcommand is now `issue-flow graphify`); docstring refreshed.
- `graphify.py` — docstrings/comments naming the user-facing `/build` / `issue-flow build` updated to `/graphify` / `issue-flow graphify`. Internal `run_build`, `_build_graphify_argv`, `_GRAPHIFY_BUILD_SUBCOMMANDS`, `_DEFAULT_BUILD_SUBCOMMAND` intentionally kept (graphify's build-the-graph concept; not user-facing).
- `dependencies.py` — Graphify `purpose` now mentions `/graphify`.
- `templating.py` — manifest entries point at `commands/graphify.md.j2` and `skills/issueflow_graphify/SKILL.md.j2`.

### Templates
- `commands/build.md.j2` → `commands/graphify.md.j2` (content updated).
- `skills/issueflow_build/SKILL.md.j2` → `skills/issueflow_graphify/SKILL.md.j2` (frontmatter `name: issueflow-graphify`, content updated).
- Cross-refs updated in `commands/iflow.md.j2`, `commands/issue-start.md.j2`, `commands/issue-close.md.j2`, `rules/issueflow-rules.mdc.j2`, `docs/cursor-issue-workflow.md.j2`.

### Repo dogfood copies + docs
- `.cursor/commands/build.md` → `.cursor/commands/graphify.md`; `.cursor/skills/issueflow-build/` → `.cursor/skills/issueflow-graphify/`.
- Cross-refs updated in `.cursor/commands/iflow.md`, `issue-start.md`, `issue-close.md`, `.cursor/rules/issueflow-rules.mdc`, `docs/cursor-issue-workflow.md`, `README.md`, `HISTORY.md`.

### Tests
- `test_cli.py`, `test_templating.py`, `test_init.py` updated to assert `graphify`. `test_graphify.py` docstrings refreshed (internal API unchanged). `test_dependencies.py` unaffected.

### Design doc
- Appended a rename note to `.issueflows/04-designs-and-guides/graphify-integration.md`.

## Verification
- `uv run pytest` → 106 passed.
- `uv run issue-flow --help` lists `graphify` (no `build`); `uv run issue-flow graphify --help` works.

## Remaining work
- None.
