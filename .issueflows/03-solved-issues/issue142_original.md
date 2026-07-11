# Issue #142: Cycling mode, stage 2: cycle state file - resumability and failure policy

Source: https://github.com/jepegit/issue-flow/issues/142

## Original issue text

Part of the **cycling mode** epic. Stage 2. Depends on #141.

## Context

A cycle can be interrupted (stop condition, editor restart, user abort). Without persistent state, the remaining queue is lost and a re-run would re-confirm from scratch.

## Scope

- Persist cycle state to `.issueflows/01-current-issues/cycle_status.md` (human-readable markdown: the confirmed queue, per-issue outcome so far, the active issue, timestamps) - same file conventions as issue status files, moved to `03-solved-issues/` when the cycle completes.
- `/iflow-cycle resume`: picks up an interrupted cycle from the state file (re-verifying each remaining issue is still open/unblocked via `agent queue`), without re-asking the original consolidated confirm for unchanged items.
- Failure policy option in the queue spec: `onfail:stop` (default) vs `onfail:skip` (record the failure, park that issue via the /iflow-pause conventions, continue the cycle).
- `/iflow-status` and `issue-flow status` mention an in-flight cycle when the state file exists.

## Acceptance criteria

- Template-contract tests for resume + onfail wording; tracking-level tests if the CLI status command learns to read the state file.
- Docs + HISTORY.

## Out of scope

Parallel dispatch (next stage).
