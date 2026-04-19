# Issue #26 status: designs-and-guides folder

- [x] Done

## Done so far

- Added `designs_folder = "04-designs-and-guides"` to `Settings` in `src/issue_flow/config.py`; included in `issueflows_subdirs` and `template_context` so the existing `_create_issueflow_dirs` loop picks it up on both `init` and `update`. No changes needed to `src/issue_flow/init.py`.
- Updated the rule template `src/issue_flow/templates/rules/issueflow-rules.mdc.j2`: added the new folder to the Issue-tracking structure tree and a new "Designs and guides" section describing purpose, when to read it, when to write it, and that `issue-flow update` never overwrites its contents.
- Updated slash-command templates to reference `{{ issueflows_dir }}/{{ designs_folder }}/`:
  - `commands/issue-plan.md.j2` — new step 1.5 "Consult existing designs / guides" and a Files-to-touch reminder when the plan expects to produce a design doc.
  - `commands/issue-start.md.j2` — sub-bullet in step 2 Implement to read relevant designs and record new design decisions.
  - `commands/issue-close.md.j2` — sanity-check bullet to confirm design decisions are captured before committing.
  - `commands/iflow.md.j2` — one-paragraph header noting the folder and that downstream commands touch it.
  - `commands/issue-yolo.md.j2` — note that if a yolo run uncovers a design decision worth recording, the change is probably too big for yolo.
- Added tests:
  - `tests/test_init.py` — extended `test_init_creates_directories` and `test_init_creates_gitkeep_files`, plus new `test_init_rule_documents_designs_folder` and `test_init_commands_reference_designs_folder`.
  - `tests/test_update.py` — new `test_update_preserves_designs_folder_contents` and `test_update_recreates_removed_designs_folder`.
  - `tests/test_config.py` — updated `test_issueflows_subdirs` count (4 -> 5) and `test_template_context_keys` to include `designs_folder`.
- Ran `uv run issue-flow update` in this repo to refresh the in-repo scaffold files so `.cursor/rules/issueflow-rules.mdc`, `.cursor/commands/*.md`, and `.cursor/skills/*` pick up the new wording, and created `.issueflows/04-designs-and-guides/.gitkeep`.
- `uv run pytest`: 68 passed, 0 failed.
- Manual verification in a scratch directory: `init` creates the folder; user content in it survives `update`; deleting the folder and running `update` recreates it with `.gitkeep`.

## Remaining work

Both tasks from the original issue are implemented:
1. Folder is created during `issue-flow init` (via `_create_issueflow_dirs` / `issueflows_subdirs`) and preserved by `issue-flow update` (user files are never manifest outputs; the folder is only recreated if missing).
2. The rule and the relevant slash commands now encourage reading from and adding to the folder.

## Deferred (not in this issue's scope)

- `docs/cursor-issue-workflow.md.j2` (public workflow overview) and the `skills/` templates under `src/issue_flow/templates/skills/` were intentionally left out of scope per the plan. They will drift slightly from the commands until updated in a follow-up.
- No dedicated `ISSUEFLOW_DESIGNS_DIR` env var was added; the folder name is a plain constant on `Settings` (same pattern as `tools_folder`, `current_issues_folder`, etc.). Easy to flip later if desired.
