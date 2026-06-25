# Issue #79 plan: new Cursor conventions

## Goal

Align issue-flow's Cursor scaffold with Cursor's newer Agent Skills convention: Cursor should be skills-first, while always-on rules remain rules and other editor profiles keep their current command behavior.

## Constraints

- Cursor's current docs/search results say Cursor 2.4+ loads project skills from `.cursor/skills/<name>/SKILL.md`, exposes skills through `/`, and includes `/migrate-to-skills` for dynamic rules and slash commands.
- The migration guidance does **not** migrate `alwaysApply: true` or glob-scoped rules, so issue-flow's always-on `.cursor/rules/issueflow-rules.mdc` should remain for Cursor unless a separate issue changes the rules surface.
- Preserve the multi-editor architecture: skills are portable for every editor, slash commands remain profile-dependent, and `AGENTS.md` remains the shared managed rules block.
- Keep implementation focused on generated scaffold behavior, docs, and tests; do not rewrite the command/skill bodies.

### Prior art

- `src/issue_flow/editors.py` defines `EditorProfile.commands_dir`; Cursor currently emits `.cursor/commands/`, while Codex already uses `commands_dir=None` and relies on skills.
- `src/issue_flow/templating.py` centralizes `COMMAND_NAMES`, `SKILL_DIRS`, and `build_manifest(profile)`, which already skips command templates when `commands_dir` is `None`.
- `src/issue_flow/init.py` writes manifest outputs per profile, upserts `AGENTS.md`, and prunes retired command/skill files during update/init.
- `tests/test_templating.py`, `tests/test_init.py`, and `tests/test_update.py` assert current Cursor command output, skill output, manifest counts, non-Cursor behavior, and update overwrite/prune behavior.
- `README.md` and `src/issue_flow/templates/docs/issue-workflow.md.j2` currently present Cursor slash commands as the primary surface and skills as optional mirrors.
- `graphify-out/GRAPH_REPORT.md` points to Community 18 (`run_init` scaffolding), Community 27 (`build_manifest` / editor output paths), Community 32 (templating tests), and Community 37 (editor-profile design) as the relevant areas.
- Prior issue #1 added skills alongside commands; the existing design doc `editor-profiles.md` says skills are the portable core and commands are niceties layered on top.

## Approach

1. Treat Cursor like Codex for command emission by setting the Cursor profile's `commands_dir` to `None`, so new Cursor scaffolds emit `.cursor/skills/`, `.cursor/rules/issueflow-rules.mdc`, `AGENTS.md`, and docs, but no `.cursor/commands/`.
2. Add a targeted cleanup path for known issue-flow command files under `.cursor/commands/` during `issue-flow update`/`init --force` so existing projects can migrate cleanly without deleting arbitrary user commands.
3. Rename the dispatcher skill output from `iflow-iflow` to `iflow`, with a compatibility prune for the old `iflow-iflow` folder, so the skills-first slash entry remains `/iflow` rather than `/iflow-iflow`.
4. Update generated docs and README to describe Cursor as skills-first, keep command sections conditional/worded for editors that still emit commands, and document that Cursor's always-on `.mdc` rule intentionally remains.
5. Update tests to lock in the new Cursor contract, preserve Claude/opencode command behavior, preserve Codex no-command behavior, and verify migration cleanup removes only known generated command files.

## Files to touch

- `src/issue_flow/editors.py` — change Cursor command surface and update comments/docstrings.
- `src/issue_flow/templating.py` — support the `iflow` skill output name and any retired skill folder tracking.
- `src/issue_flow/init.py` — prune known generated Cursor command files when Cursor no longer emits commands.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — make command vs skill wording profile-aware.
- `src/issue_flow/templates/skills/iflow_iflow/SKILL.md.j2` or renamed template folder — make the dispatcher skill emit as `iflow`.
- `README.md` — update the scaffold tree, editor support table, and Cursor usage prose.
- `tests/test_editors.py`, `tests/test_templating.py`, `tests/test_init.py`, `tests/test_update.py` — update expectations and add migration coverage.
- `.issueflows/04-designs-and-guides/editor-profiles.md` — record the Cursor skills-first decision after implementation.

## Test strategy

- `uv run ruff check src/ tests/`
- `uv run pytest`
- End-to-end scaffold check in a throwaway git repo: `uv run --project /workspace issue-flow init . --skip-dep-check`, then verify `.cursor/skills/` and `.cursor/rules/issueflow-rules.mdc` exist while `.cursor/commands/` does not.
- Update migration check in a throwaway repo with pre-existing known `.cursor/commands/iflow*.md` files, then run `uv run --project /workspace issue-flow update . --skip-dep-check` and verify generated commands are removed but unrelated user command files remain.

## Open questions

- Accept the breaking scaffold change for Cursor now: new Cursor installs no longer get `.cursor/commands/*.md`, relying on skill slash entries instead.
- Accept renaming the dispatcher skill from `iflow-iflow` to `iflow` as part of this same issue, because otherwise Cursor's skills-first primary entry point becomes awkward.
