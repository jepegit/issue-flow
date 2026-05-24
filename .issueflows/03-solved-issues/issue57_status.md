# Status for issue #57: /issue-plan: add explicit 'prior-art discovery' step (codebase grep + graph hubs)

- [x] Done

## What was done

- Added **step 1.75 Prior-art discovery** to `/issue-plan`: optional graphify skim of `graphify-out/GRAPH_REPORT.md`, grep for adjacent helpers, record under `### Prior art` in plan `## Constraints`, strong overlaps → `## Open questions`.
- Updated the plan-file template example with a `### Prior art` sub-section (including `- None found (grep + graph checked).` when applicable).
- Mirrored the checklist in the `issueflow-issue-plan` skill.
- `/issue-start` and `issueflow-issue-start` now remind the agent to read `### Prior art` from the confirmed plan before writing new modules.
- `/issue-yolo` documents that trivial runs may abbreviate prior-art to a quick grep (skip graph skim).
- Updated `docs/cursor-issue-workflow.md` to describe the new planning step.
- Added templating tests for prior-art keywords; added `designs_folder` to test context.

## Tests

- `uv run pytest -q` → 106 passed.

## Remaining work

None.
