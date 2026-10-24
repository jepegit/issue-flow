# Status — issue #409

- [x] Done

## Done

- Rewrote `.issueflows/00-tools/verify_scaffold.py` for the eleven-command surface:
  - The expected files now come from `issue_flow.templating`: `DEFAULT_SKILL_DIRS`, `skill_output_name` and `skill_side_output_names`. Every router and mode file must render for cursor and claude.
  - Retired names must be absent. Skill folders are checked against `STEM_RENAMES` and command files against `RETIRED_COMMANDS`.
  - Each marker now points at the file that carries it: pick label lanes, `close/merge.md` / `ops.md` / `version.md`, `run/yolo.md`, build early PR, and the `AGENTS.md` rule body.
- Replaced markers that no longer exist with their current wording:
  - `### pstack skills` → `- **pstack** (unslop, tdd)`
  - `Unslop (pstack, optional)` → "*Offer* the `unslop` skill"
  - novice `/iflow-setup` → the `` `iflow-setup` `` row in the AGENTS.md table
  - `iflow-capture` → `iflow-pick/capture.md`
  - `Label-driven yolo/ops flow` → "Fold the yolo confirm / ops lane into the pick confirm"
- Added `label_flows = false` checks for the publish-label section and the rule's label-routing line.
- Updated the `00-tools/README.md` row.

## Verification

- `uv run .issueflows/00-tools/verify_scaffold.py`: exit 0, 169 checks pass.
- Regression injected and reverted: removing `iflow_close/ops.md.j2` gives exit 1 with 4 failures.
- Regression injected and reverted: dropping the yolo lane from `iflow_pick/SKILL.md.j2` gives exit 1 with 8 failures.
- `uv run pytest`: 967 passed. Essential tests: 40 passed. Ruff is clean on the tool.

## Remaining

None.
