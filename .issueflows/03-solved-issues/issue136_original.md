# Issue #136: Epic planning, stage 1: /iflow-epic skill + 05-epics scaffold (draft-only)

Source: https://github.com/jepegit/issue-flow/issues/136

## Original issue text

Part of the **staged planning mode** epic (extends #12). Stage 1, issue 1 of 2.

## Context

One issue = one branch = one PR works for small changes. Larger changes need an **epic**: a plan divided into sequential **stages**, each stage broken into manageable issues that flow through the normal lifecycle.

## Scope

- New scaffolded folder `.issueflows/05-epics/` (created by init/update like the other numbered folders; user content never overwritten).
- Epic plan template `epic<N>_plan.md` with structure: Goal / Constraints / Stages, where each stage lists issue specs (title, one-paragraph spec, dependencies as "Depends on #N", explicit yolo-fitness judgment per the yolo label criteria).
- New `/iflow-epic` skill (+ command twin where supported): interviews/drafts the staged plan for a named GitHub issue (the epic anchor), writes `epic<N>_plan.md`, stops for confirmation. **Draft-only: no GitHub writes in this issue** (publishing is the next issue).
- Off-path: never auto-dispatched by /iflow.
- Mode placement: standard mode only (simple mode omits it).

## Acceptance criteria

- `issue-flow init`/`update` create `05-epics/` and install the skill (template-contract tests in test_init style).
- Rendered skill documents the stage/issue-spec structure, the yolo-fitness judgment step, and the draft-only boundary.
- docs/issue-workflow template + docs updated; HISTORY entry.

## Out of scope

Publishing issues to GitHub, /iflow-pick integration, epic-status CLI (later issues in this epic).
