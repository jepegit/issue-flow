# Issue #140: Cycling mode, stage 1: deterministic issue-flow agent queue CLI

Source: https://github.com/jepegit/issue-flow/issues/140

## Original issue text

Part of the **cycling mode** epic. Stage 1, issue 1 of 2. No dependencies (can start immediately).

## Context

Before an agent can cycle through many issues hands-off, something deterministic must decide **which issues, in which order, and which are blocked**. Same "CLI for facts" pattern as `agent state` / `agent version-plan`.

## Scope

- New read-only command: `issue-flow agent queue [N N ...] [--label L] [--epic N] [-C DIR] [--json]`.
- Sources: an explicit issue-number list, a GitHub label (open issues via `gh issue list --label`), or an epic''s current stage (reuse the epic-status parser when #138 lands; otherwise label/list only and note the gap).
- Parses `Depends on #N` / `Blocked by #N` lines from issue bodies; produces a **topological order**, a `blocked` list (open dependencies), and flags per issue: `yolo` label present, dependency depth, and `independent: true/false` (no dependency relation to any other queue member - the parallelism signal for a later stage).
- Cycle detection: a dependency cycle is reported (exit 1, naming the cycle), never silently broken.
- Graceful gh degradation like the other agent commands.

## Acceptance criteria

- Unit tests for the dependency parser + toposort (incl. cycle case); CLI tests with mocked gh.
- agent sub-app help, docs/cli.md row, HISTORY entry; template-CLI consistency suite passes.

## Out of scope

Any execution of issues; the /iflow-cycle skill (next issue).

**yolo-fitness:** additive read-only CLI, proven pattern, crisp criteria, testable in isolation -> labeled `yolo`.
