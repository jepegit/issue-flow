# Issue #415 plan

## Goal

Add `/iflow-run direct` so a capable model finishes one issue without a plan gate or mid-run questions, using graphify and the agent CLI, and still files status, essential-test bookkeeping, and changelog trailers. The run opens or updates the PR and stops there.

## Constraints

- Templates under `src/issue_flow/templates/` are the source of truth. Edit those, then re-render the dogfood scaffold with `issue-flow update`.
- Stay inside `tests/test_command_surface.py` budgets (`SKILL_BUDGET` 1600, `SIDE_BUDGET` 3000, `RULE_BUDGET` 900, `WORKFLOW_DOC_BUDGET` 1500).
- `MODE_PROHIBITION_CAP` is 48 and the current mode files already sit on that cap. `direct.md.j2` adds zero `do not` / `don't` / `never` / `must not`. State stops as "Stop when …".
- Mode file is plain markdown: no frontmatter, no `MODEL & EXECUTION DIRECTIVE`.
- Leave yolo, cycle, auto, drive, and the `hands_off` knob behaving as they do now.
- No new scaffolding mode, no `fable` command name, no pick label, no auto-merge, no `/iflow-cleanup`, no `graphify extract`.

### Prior art

- `skill_side_templates()` in `src/issue_flow/templating.py` discovers every `*.md.j2` beside `SKILL.md.j2`. A new side file renders on `issue-flow update` with no filename registry. Community 36 in `graphify-out/GRAPH_REPORT.md` (God node neighbourhood of `render_template` / `skill_side_templates`). `graphify query` for this area only hit archived plan notes; the report was the useful graph.
- `COMMANDS` in the same module: the `iflow-run` modes cell is `` `yolo`, `cycle`, `auto`, `drive` ``. That cell feeds the always-on rule and the workflow-doc table.
- `src/issue_flow/templates/skills/iflow_run/yolo.md.j2` is the chain to mirror. It still writes a short plan and calls `close yolo` (merge, then default branch). Direct skips the plan file and calls ordinary close.
- `tests/test_command_surface.py`: `test_merged_skills_ship_mode_files` hardcodes the `iflow_run` side set, `test_router_names_every_mode_file` requires the router to name each side file, `test_run_router_and_modes` lists the four modes.
- `.issueflows/00-tools/verify_scaffold.py` derives the rendered file list from `templating`, so a new side file is checked automatically. Its yolo marker assertions stay as they are.
- Design notes for hands-off flows live as sections in `.issueflows/04-designs-and-guides/hands-off-runs.md`.

## Approach

1. Add `src/issue_flow/templates/skills/iflow_run/direct.md.j2`. Invocation is the authorization, including when `hands_off` is false. No second confirm.

   Preflight, then stop on failure:

   - Current branch is the default branch and the tree is dirty, or home is not the default branch: stop. When home is the default branch and clean, create the issue worktree with `issue-flow agent worktree-add <N> --slug <slug>` and continue there.
   - Unrelated dirty paths: stop.
   - Documented tests fail up front: stop. When `essential_tests` is true the up-front gate is `pytest -m essential` via the project runner; otherwise the project's documented test command.

   Chain:

   - Resolve `<N>` from the argument, else the focus issue (`issue-flow agent state --json`). Capture through `capture.md` when `issue<N>_original.md` is missing. An archived group under `02-partly-solved-issues/` or `03-solved-issues/` stops the run.
   - Skip `issue<N>_plan.md`. Record decisions in `issue<N>_status.md` as the work proceeds.
   - Implement. When `graphify-out/graph.json` exists, run `graphify query` / `path` / `explain` before a broad search. After code edits, run `issue-flow graphify` (AST `update` only). A missing or failing graphify is one report; continue with grep. Prefer `issue-flow agent … --json`. Read the design note that matches the area.
   - Tests again, same gate as preflight. When `essential_tests` is true, write the registry row for tests this issue added or changed (mark vs unmarked) with no confirm.
   - Close without the `yolo` token: status checkbox, move the group by that checkbox, changelog trailers (`Changelog`, `Changelog-Date`, `Changelog-Id`), leave `HISTORY.md` unedited on the issue branch, commit, `issue-flow agent sync-branch`, push, open or update the PR (`Closes #N`). Stop with the PR URL. The issue branch stays checked out. Cleanup stays with the user.

   Safety stops (one line each, no menu): failing tests, `sync-branch` exit 1, ambiguous repo, product-code conflict, destructive git. Several independent deliverables: stop and name `/iflow-issue epic` or `/iflow-issue split`. This mode creates no children.

2. Router `skills/iflow_run/SKILL.md.j2`: add the `direct [<N>]` → `direct.md` row and mention it in the description. Shared rules: yolo / cycle / auto / drive still ask once; direct's invocation is that confirm. Direct stops on the issue branch with the PR open; the other modes still leave a clean default branch when they stop.

3. `COMMANDS` modes cell for `iflow-run`: append `` `direct` `` so the rule table and the workflow-doc table both list it.

4. One sentence in `docs/issue-workflow.md.j2` under "Where the agent stops to ask": `/iflow-run direct` treats the invocation as its confirm, skips the plan gate, and opens a PR without merging.

5. Short section in `hands-off-runs.md`: direct is the capable-model path (no plan file, PR left open). Yolo remains the small-fix path that merges. `hands_off` still runs the plan step on the interactive lifecycle. Auto and drive remain the epic path.

6. Re-render with `uv run issue-flow update` so `.cursor/skills/iflow-run/` and the managed rule block match the templates.

## Files to touch

- `src/issue_flow/templates/skills/iflow_run/direct.md.j2` — new mode file.
- `src/issue_flow/templates/skills/iflow_run/SKILL.md.j2` — router row, description, shared-rule clause.
- `src/issue_flow/templating.py` — `COMMANDS` modes cell.
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — one sentence.
- `.issueflows/04-designs-and-guides/hands-off-runs.md` — design section.
- `tests/test_command_surface.py` — side-file set and `test_run_router_and_modes` include `direct`; assert the rendered mode names graphify query/update, changelog trailers, and ordinary close (no `close yolo`, no `gh pr merge`).
- Dogfood render: `.cursor/skills/iflow-run/SKILL.md`, `.cursor/skills/iflow-run/direct.md`, `AGENTS.md` managed block, `docs/issue-workflow.md` (whatever `issue-flow update` rewrites from these templates).

## Test strategy

- `uv run pytest tests/test_command_surface.py tests/test_templating.py`
- `uv run ruff check src/ tests/`
- `uv run .issueflows/00-tools/verify_scaffold.py` after the template lands.
- Full `uv run pytest` before close. This repo has `essential_tests = true`; the in-loop gate for later close is `uv run pytest -m essential`.
- Extend the existing command-surface tests. Add no new essential mark and no new registry row unless close review finds a new test function that belongs in the registry.

## Open questions

- None. The issue text already fixes the name (`direct`), the no-merge stop, and the bookkeeping that stays.
