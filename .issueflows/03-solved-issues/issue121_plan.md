# Issue #121 plan: skill version stamp

## Goal

Let users verify scaffolded skills match their installed `issue-flow` version by stamping each rendered `SKILL.md` with the package version.

## Constraints

### Prior art

- `issue_flow.config.Settings.template_context()` — Jinja context for all templates.
- `issue_flow.init._write_manifest_files()` — renders and writes manifest entries.
- `issue_flow.__version__` / `issue-flow --version` — existing version source.
- `skill-authoring.md` — skills use YAML frontmatter; keep Jinja includes intact.

## Approach

1. Add `issue_flow_version` to `template_context` (from `issue_flow.__version__`).
2. Add `stamp_skill_version(content, version)` in `templating.py` — inject or refresh `issue-flow-version: <ver>` in YAML frontmatter (fallback HTML comment when no frontmatter).
3. Apply stamp in `_write_manifest_files` for every `skills/*/SKILL.md.j2` output.
4. Re-render this repo via `issue-flow update`.
5. Document one-liner check in workflow doc template: compare `issue-flow --version` with `grep issue-flow-version .cursor/skills`.

## Files to touch

- `src/issue_flow/config.py` — context key
- `src/issue_flow/templating.py` — stamp helper + export
- `src/issue_flow/init.py` — apply stamp on skill write
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — brief how-to-check note
- `tests/test_templating.py` — unit tests for stamp helper
- `tests/test_update.py` — integration: updated skills carry version
- Re-rendered `.cursor/skills/**/SKILL.md` via update

## Test strategy

- `uv run pytest` — new unit + update tests; full suite green.
- `uv run ruff check src/ tests/`
