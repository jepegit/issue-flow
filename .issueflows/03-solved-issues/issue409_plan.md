# Plan — issue #409: verify_scaffold.py is stale since #406

Plan confirmed via `/iflow-run yolo` consolidated confirm (2026-10-24).

## Goal

`uv run .issueflows/00-tools/verify_scaffold.py` exits 0 on `main` and again catches real regressions on the merged eleven-command surface.

## Approach

- Derive the expected surface from `issue_flow.templating`. Use `DEFAULT_SKILL_DIRS`, `skill_output_name` and `skill_side_output_names` to require every router and mode file. Use `STEM_RENAMES` and `RETIRED_COMMANDS` to require that retired skill folders and command files are absent.
- Point each marker at the file that carries it now:
  - pick router: label lanes
  - `close/merge.md`: `--squash --auto`
  - `close/ops.md`: ops path
  - `close/version.md`: publish label
  - `run/yolo.md`: `/iflow-close yolo`
  - build router: early PR
  - root `AGENTS.md`: rule body
- Markers that disappeared become their current equivalents:
  - `### pstack skills` → `- **pstack** (unslop, tdd)`
  - `Unslop (pstack, optional)` → "*Offer* the `unslop` skill"
  - the novice `/iflow-setup` check → `` `iflow-setup` `` in the AGENTS.md command table
  - `iflow-capture` → `iflow-pick/capture.md`
- Keep the five groups and the `--keep` flag. Refresh the docstring and the `00-tools/README.md` row.

## Files to touch

- `.issueflows/00-tools/verify_scaffold.py`
- `.issueflows/00-tools/README.md`

## Test strategy

- Run the tool on the branch and expect exit 0.
- Regression checks, each reverted afterwards: delete `iflow_close/ops.md.j2` and expect non-zero; drop the yolo label lane in `iflow_pick/SKILL.md.j2` and expect non-zero.
- `uv run pytest`, then `ruff check` on the tool.
