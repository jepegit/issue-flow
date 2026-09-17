# Issue #277 plan

## Goal

`issue-flow doctor` / `agent audit` report skill directories under each in-use
editor skills path that are **not** packaged issue-flow output names. Read-only.

## Constraints

- Report-only. No delete, prune, import, or `doctor --fix` action.
- Compare against **all** `SKILL_DIRS` output names (`skill_output_name`),
  including optional pstack stems — those are still packaged.
- INFO severity (same class as `missing_editor_scaffold`); does not fail
  doctor (exit 1 is error-only).
- Do not add `skillbook-lessons.md` here — #275 owns that file; its follow-up
  table already links #277.
- Out of scope: #276 clobber protection, #268 lint, skillbook CLI.

### Prior art

- `audit_editor_scaffolds()` in `agent.py` — same doctor hook, INFO findings,
  skip when `ISSUEFLOW_AGENT_DIR` overrides layout.
- `skill_output_name()` / `SKILL_OUTPUT_NAMES` in `templating.py` — stem →
  on-disk folder (`iflow_plan` → `iflow-plan`, `iflow_iflow` → `iflow`,
  pstack stems → upstream names).
- `_prune_excluded_surfaces()` in `init.py` — only touches `SKILL_DIRS`
  names; user folders already left alone. This issue only makes them visible.
- `DirtyFinding` + `run_audit` JSON (`findings[].code`).
- Toolbox: no helper needed.

## Approach

1. Helper `packaged_skill_output_names()` → frozenset of output folder names
   for every stem in `SKILL_DIRS`.
2. `audit_unmanaged_editor_skills(project_root, settings)`:
   - If `agent_dir_override`: skip (same as `audit_editor_scaffolds` — profile
     paths no longer describe the tree).
   - Else, for each `EditorProfile` whose `<agent_dir>/skills/` exists, list
     immediate **directories** whose names are not in the packaged set.
     Skip non-dirs and dot-names.
   - One INFO finding per path, code `unmanaged_editor_skill`,
     `repairable=False`, message names the relative path.
3. `run_audit` extends findings with this list (after editor-scaffold check).
4. Document the code in `dirty-issueflows.md`; one sentence in `docs/cli.md`.

## Files to touch

- `src/issue_flow/templating.py` — `packaged_skill_output_names()`.
- `src/issue_flow/agent.py` — scan + hook into `run_audit`.
- `tests/test_cli.py` — extra folder listed; packaged names not listed;
  `--fix` does not delete the extra folder.
- `.issueflows/04-designs-and-guides/dirty-issueflows.md` — new row.
- `docs/cli.md` — mention unmanaged skill dirs.

## Test strategy

`uv run pytest`. New CLI tests on a seeded clean tree plus
`.cursor/skills/my-notes/` and a packaged `iflow-plan/` sibling.

## Open questions

None — yolo auto-confirm. Scope is small.
