# Issue #137: Epic planning, stage 1: publish a confirmed epic plan to GitHub issues

Source: https://github.com/jepegit/issue-flow/issues/137

## Original issue text

Part of the **staged planning mode** epic (extends #12). Stage 1, issue 2 of 2. Depends on #136.

## Context

After `/iflow-epic` writes and the user confirms `epic<N>_plan.md`, the plan must become real GitHub issues â€” stage by stage, not all at once, so later stages can be re-planned from what stage 1 taught us.

## Scope

- Extend `/iflow-epic` with a `publish [stage <k>]` action: for each issue spec in the stage, `gh issue create` with a self-contained body (context, scope, acceptance criteria, "Depends on #N" lines, link back to the epic issue), applying the `yolo` label only when the spec passes the yolo-fitness criteria.
- Maintain a **task list in the epic issue body** (`- [ ] #N`) so GitHub renders progress; append stage sections as they are published.
- One consolidated confirm before creating anything (destructive-ish: outward-facing writes); dry-run listing first.
- Record published issue numbers back into `epic<N>_plan.md`.

## Acceptance criteria

- Publishing a stage creates the issues, updates the epic task list, and is idempotent (re-running skips already-published specs by recorded number).
- Template-contract tests for the new skill sections; docs + HISTORY.

## Out of scope

Automatic milestone creation (note as follow-up), /iflow-pick integration, epic-status CLI.
