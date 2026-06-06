# Status — issue #62: Make issue-flow editor-agnostic

- [x] Done

## Done so far

- Added `src/issue_flow/editors.py`: `EditorProfile` + `EDITORS` registry
  (`cursor`, `claude`, `opencode`, `codex`), `get_profile`, `resolve_editors`
  (handles `all`, dedupe, case-insensitive, validation).
- `config.py`: `ISSUEFLOW_EDITOR` setting (default `cursor`); `agent_dir`
  derived from the profile unless `ISSUEFLOW_AGENT_DIR` is set; context now
  carries `editor`, `editor_name`, `commands_dir`, `graphify_installer`.
- `templating.py`: `TEMPLATE_MANIFEST` -> `build_manifest(profile)` (skills
  always; commands only when `commands_dir`; per-editor rules extra; neutral
  `docs/issue-workflow.md`). Added `{commands_dir}` placeholder. Kept a
  back-compat `TEMPLATE_MANIFEST = build_manifest(cursor)`.
- Templates: new `rules/_body.md.j2` partial included by `issueflow-rules.mdc.j2`,
  `CLAUDE.md.j2`, and `AGENTS.md.j2` (single source of truth). Renamed
  `docs/cursor-issue-workflow.md.j2` -> `docs/issue-workflow.md.j2`. De-Cursored
  wording (graphify command/skill, docs, rules body) using `{{ editor_name }}`
  and `graphify_installer` conditionals.
- `init.py`: per-editor scaffold loop; `_ensure_agents_md` writes a
  marker-delimited managed block into `AGENTS.md` (create / refresh-in-place /
  append; never clobbers user content); graphify gated on
  `profile.graphify_installer`; `_already_initialized` uses `build_manifest`;
  unknown editor exits cleanly (code 2).
- `graphify.py`: `register_with_cursor` -> `register_with_editor(.., installer)`.
- `cli.py`: repeatable `--editor` / `-e` (accepts `all`) on `init` and `update`.
- README: new "Editor support" section, `--editor` rows, config table updates
  (`ISSUEFLOW_EDITOR`, profile-derived `ISSUEFLOW_AGENT_DIR`), Future-plans bullet.
- Tests: new `tests/test_editors.py`; `build_manifest` + no-Cursor-leakage tests;
  AGENTS.md managed-block + multi-editor init tests; AGENTS.md refresh + Claude
  update tests; CLI `--editor` tests. Updated context-keys and docs-filename tests
  and the graphify-register rename.

## Verification

- `uv run pytest` — 140 passed.
- `uv run ruff check src/ tests/` — all checks passed.

## Remaining work

- None for this issue. Deferred (noted in plan, out of scope): deep per-editor
  command/skill divergence for Codex (slash-command-free phrasing beyond the
  shared note) — track separately if wanted.
