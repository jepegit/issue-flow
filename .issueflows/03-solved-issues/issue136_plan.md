# Plan — Issue #136: /iflow-epic skill + 05-epics scaffold (draft-only)

Part of epic #144 (staged planning mode), stage 1.

## Goal

A new workflow surface for planning larger changes: `/iflow-epic <N>` drafts a
staged plan (`epic<N>_plan.md` under a new `.issueflows/05-epics/` folder)
where each stage lists manageable issue specs. Draft-only: this issue makes no
GitHub writes; publishing is #137.

## Constraints

- Standard mode only (simple mode's explicit surface lists exclude it
  automatically since standard uses "all").
- Off-path: `/iflow` never auto-dispatches to it; enumerations updated.
- step_profiles.toml must gain `iflow_epic` (loader hard-fails on missing
  lifecycle stems) — profile `reasoning` (planning-heavy).
- The plan file defines the contract #137 publishes: per-issue spec with
  title, body outline, `Depends on:` lines (published `#N` or unpublished
  `stage <j> issue <k>` placeholders), and a yolo-fitness judgment.

## Approach

1. `config.py`: `epics_folder = "05-epics"` + `issueflows_subdirs` + template
   context key.
2. `templating.py`: `iflow-epic` in COMMAND_NAMES, `iflow_epic` in SKILL_DIRS.
3. `step_profiles.toml`: `iflow_epic = "reasoning"`.
4. New `templates/skills/iflow_epic/SKILL.md.j2` (the playbook: read the epic
   issue, draft stages + issue specs with sizing rules and yolo judgments,
   iterate with the user, stop before any GitHub write) + command twin.
5. Off-path enumerations: `commands/iflow.md.j2`, `skills/iflow_iflow`,
   rules `_body.md.j2`, workflow doc table + section.
6. Tests (test_init: folder + gitkeep + skill content), docs, HISTORY,
   scaffold regen.

## Test strategy

Template-contract tests: 05-epics folder + .gitkeep created; rendered skill
asserts draft-only boundary, stage structure, yolo-fitness step, off-path
constraint; simple mode omits the surface; step-profile loader passes (full
suite import).
