# Issue #138: Epic planning, stage 2: deterministic issue-flow agent epic-status CLI

Source: https://github.com/jepegit/issue-flow/issues/138

## Original issue text

Part of the **staged planning mode** epic. Stage 2, issue 1 of 2. Depends on #136 and #137.

## Context

Agents (and /iflow-pick, /iflow-cycle later) need a deterministic answer to "where does epic N stand?" instead of re-deriving it from markdown + GitHub each time. Same pattern as `agent state` / `agent version-plan`: CLI for facts, prompts for judgment.

## Scope

- New read-only command: `issue-flow agent epic-status <N> [-C DIR] [--local] [--json]`.
- Parses `.issueflows/05-epics/epic<N>_plan.md` (stages, issue specs, recorded issue numbers, "Depends on #N" lines) and â€” unless `--local` â€” cross-references `gh issue list/view` states.
- JSON payload: `{epic, stages: [{index, title, issues: [{number, title, state, blocked_by, yolo}], done, open, blocked}], current_stage, next_candidates}` where `next_candidates` are open, unblocked issues of the current stage (dependencies all closed).
- Graceful degradation exactly like `agent state`: missing gh never hard-fails; missing plan file exits 1 with a hint.

## Acceptance criteria

- Unit tests for the plan-file parser (fixtures with multiple stages/deps); CLI tests with mocked gh (existing `_fake_runner` pattern in test_gitutils / monkeypatch pattern in test_cli).
- Registered in the agent sub-app help; row in docs/cli.md; HISTORY entry.
- Template-CLI consistency suite passes (any skill referencing the command must match).

## Out of scope

Any writes; /iflow-pick integration (next issue).

**yolo-fitness:** additive read-only CLI following the proven agent-subcommand pattern, crisp acceptance criteria, guarded by the existing test conventions -> labeled `yolo`.
