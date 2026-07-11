# Issue #139: Epic planning, stage 2: /iflow-pick and /iflow epic awareness + stage gates

Source: https://github.com/jepegit/issue-flow/issues/139

## Original issue text

Part of the **staged planning mode** epic. Stage 2, issue 2 of 2. Depends on #138.

## Context

With epics published and epic-status queryable, the daily-driver commands should navigate them: picking the next issue should prefer the active epic, and finishing a stage should close the loop.

## Scope

- `/iflow-pick`: when exactly one epic has open issues (or the user names one, e.g. `iflow pick epic 140`), prefer its **current stage''s unblocked issues** in the ranking; use `issue-flow agent epic-status --json` as the fast path.
- **Stage gate**: when the last issue of a stage closes (detected during /iflow-close or /iflow-cleanup of an epic-linked issue), offer to (a) post a stage-summary comment on the epic issue and (b) run `/iflow-epic publish` for the next stage. Offer only - never auto-publish.
- Rules/workflow-doc mentions so agents know epics exist.

## Acceptance criteria

- Template-contract tests: pick skill mentions epic preference and the fast path; close/cleanup mention the stage gate offer.
- Docs + HISTORY.

## Out of scope

Cycling through the issues hands-off (that is the cycling-mode epic).
