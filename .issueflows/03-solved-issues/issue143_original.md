# Issue #143: Cycling mode, stage 3: parallel dispatch for independent issues (experimental)

Source: https://github.com/jepegit/issue-flow/issues/143

## Original issue text

Part of the **cycling mode** epic. Stage 3 (experimental, harness-dependent). Depends on #140 and #141.

## Context

When the harness supports it (Cursor background agents, Claude Code subagents/worktrees), independent issues could run in parallel. This is deliberately last: parallelism multiplies failure modes (merge races, shared-file conflicts like HISTORY.md, CI contention) and must never be required for the sequential core to work.

## Scope

- Use `agent queue --json` `independent` flags: only issues with **no dependency relation to any other queue member** qualify.
- Pattern: one **git worktree per issue** (`git worktree add`), each running its own yolo chain; PRs merged **serially** by the coordinating session (rebase/re-run tests on refusal), worktrees pruned after.
- Shared-file mitigation: HISTORY.md updates deferred to the serial merge step (the coordinator appends bullets in merge order), never written concurrently.
- Skill support: `/iflow-cycle ... parallel:<n>` opt-in cap; refuse when the harness lacks background execution (document detection heuristics per editor).
- A design doc under `04-designs-and-guides/` recording the constraints and per-harness notes, since capabilities move fast.

## Acceptance criteria

- Design doc + skill sections with template-contract tests; sequential mode remains the default and untouched.
- Docs + HISTORY.

## Out of scope

Cross-repo parallel cycles (workspace registry integration is a possible follow-up).
