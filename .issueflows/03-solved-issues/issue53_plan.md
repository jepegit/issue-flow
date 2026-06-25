# Plan for issue #53: Add a project-summary doc (this-project.md) generated/maintained by issue-flow

## Goal

Add a durable, hand-editable project brief at `.issueflows/04-designs-and-guides/this-project.md` so agents and humans have a predictable orientation file that `issue-flow init` and `issue-flow update` can create when missing without clobbering user edits.

## Constraints

- Follow this repo's uv-managed Python tooling; implementation/test commands should use `uv run ...`.
- The project brief is user-owned durable memory, not a packaged scaffold output that should be overwritten by `issue-flow update` or `issue-flow init --force`.
- Keep v1 placeholder-based. Do not add `--autofill-project` or parsers for `pyproject.toml`, `package.json`, or README content in this issue.
- Keep the output editor-neutral and single-copy, even when `--editor all` renders multiple editor profiles.
- Relevant design docs:
  - `.issueflows/04-designs-and-guides/editor-profiles.md` - one shared template tree with editor-specific profile differences; `AGENTS.md` is handled outside `build_manifest`.
  - `.issueflows/04-designs-and-guides/python-toolchain-deference.md` - shared rules body is the source of truth for agent instructions and should remain editor-neutral.

### Prior art

- `build_manifest()` (`src/issue_flow/templating.py`) - convention: package-owned commands, skills, editor rules extras, and `docs/issue-workflow.md` are manifest entries; `run_update` overwrites manifest outputs. New work: coexist outside the manifest so `this-project.md` is not overwritten.
- `_write_manifest_files()` (`src/issue_flow/init.py`) - convention: `force=False` skips existing manifest files, `force=True` overwrites them. New work: do not reuse this for the project brief because the brief must stay user-owned even under update/force.
- `_ensure_agents_md()` and `_ensure_dotenv_file()` (`src/issue_flow/init.py`) - convention: special non-manifest writers preserve user content and only create/append/update managed sections. New work: mirror this "ensure" pattern with an `_ensure_project_brief()` helper that creates the file only when missing.
- `_create_issueflow_dirs()` and `Settings.designs_folder` (`src/issue_flow/init.py`, `src/issue_flow/config.py`) - convention: `.issueflows/04-designs-and-guides` is a first-class subdirectory. New work: write `this-project.md` under that configured durable-memory folder.
- `test_update_preserves_designs_folder_contents()` (`tests/test_update.py`) - convention: update must not touch user content in `04-designs-and-guides`. New work: extend this behavior with explicit tests for the project brief.
- Graph checked: `graphify-out/GRAPH_REPORT.md` highlights template/render/init communities (notably Community 0 around `render_template()` / `build_manifest()` and Community 2 around `run_init()` / directory creation), matching the code paths above.

## Approach

1. Add a new Jinja template for the brief, `src/issue_flow/templates/docs/this-project.md.j2`, with concise placeholder sections:
   - What this project is
   - Stack / runtime
   - How to run / test
   - Conventions
   - Entry points
   - Non-goals / known limitations
2. Add an `_ensure_project_brief(project_root, settings, context)` helper in `src/issue_flow/init.py`.
   - Path: `project_root / settings.issueflows_dir / settings.designs_folder / "this-project.md"`.
   - If missing, render `docs/this-project.md.j2` and write it.
   - If present, print a skip message and leave bytes unchanged.
   - Do not include it in `build_manifest()`, because update refreshes manifest outputs with `force=True`.
3. Call `_ensure_project_brief` once from `run_init` and once from `run_update`, after `_create_issueflow_dirs`.
   - Use the first resolved editor profile only for template context, because the file is editor-neutral and should be generated once.
   - Preserve the file even when `run_init(..., force=True)` is used.
4. Update scaffolded orientation text:
   - In `templates/rules/_body.md.j2`, tell agents to skim `{{ issueflows_dir }}/{{ designs_folder }}/this-project.md` before planning/implementation when present.
   - In `templates/commands/iflow-plan.md.j2` and `templates/skills/iflow_plan/SKILL.md.j2`, add the project brief to the read-context step.
   - In `templates/commands/iflow-start.md.j2` and `templates/skills/iflow_start/SKILL.md.j2`, add the same implementation-time reminder.
   - Update `templates/docs/issue-workflow.md.j2` and `README.md` so humans know the brief is created and user-owned.
5. Add/update tests:
   - `tests/test_init.py`: `run_init` creates `.issueflows/04-designs-and-guides/this-project.md`; re-running init and `force=True` do not overwrite customized content.
   - `tests/test_update.py`: `run_update` creates the brief when missing and preserves customized content when present.
   - `tests/test_templating.py`: the new template renders with the default context; rules/plan/start command and skill templates mention `this-project.md`.
6. During implementation, add a short design note under `.issueflows/04-designs-and-guides/` documenting the non-manifest ensure-helper choice, since it is a durable scaffold behavior decision.

## Files to touch

- `src/issue_flow/templates/docs/this-project.md.j2` - new project-brief template.
- `src/issue_flow/init.py` - add and call `_ensure_project_brief`.
- `src/issue_flow/templates/rules/_body.md.j2` - mention the project brief in agent orientation guidance.
- `src/issue_flow/templates/commands/iflow-plan.md.j2` - include the brief in planning context.
- `src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2` - mirror the command guidance.
- `src/issue_flow/templates/commands/iflow-start.md.j2` - include the brief in implementation context.
- `src/issue_flow/templates/skills/iflow_start/SKILL.md.j2` - mirror the command guidance.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` - document the generated durable project brief.
- `README.md` - update the generated tree/usage docs.
- `tests/test_init.py` - init and force-preservation coverage.
- `tests/test_update.py` - update create/preserve coverage.
- `tests/test_templating.py` - render/reference coverage.
- `.issueflows/04-designs-and-guides/project-brief-scaffold.md` - design note for the non-manifest, create-if-missing behavior.

## Test strategy

- `uv run pytest tests/test_init.py tests/test_update.py tests/test_templating.py`
- `uv run pytest`
- `uv run ruff check src/ tests/`
- After code changes, run `graphify update .` to refresh the local AST knowledge graph.

## Open questions

- None for v1. This plan chooses the issue's preferred durable location (`.issueflows/04-designs-and-guides/this-project.md`), keeps the file name `this-project.md`, and defers autofill behavior to a future issue.
