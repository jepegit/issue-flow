# Issue #141: Cycling mode, stage 1: /iflow-cycle skill - sequential hands-off issue loop

Source: https://github.com/jepegit/issue-flow/issues/141

## Original issue text

Part of the **cycling mode** epic. Stage 1, issue 2 of 2. Depends on #140.

## Context

`/iflow-yolo` handles one small issue hands-off. Users with a stack of small issues want to process **many in a row** with a single up-front confirmation, and be interrupted only when strictly necessary.

## Scope

- New `/iflow-cycle <queue-spec>` skill (+ command twin), off-path, standard mode only. Queue spec: explicit numbers, `label:<L>`, or `epic <N> [stage <k>]`; resolved via `issue-flow agent queue --json`.
- **One consolidated confirm** up front: list the ordered queue (skipping blocked issues, saying why), state that each issue runs the full yolo chain (init -> plan -> start -> close yolo, PR auto-merged, switchback), and get one yes.
- Per-issue execution: reuse the existing yolo chain verbatim, including its safeguards (clean tree, passing tests) - a safeguard failure is a **stop condition**, not a skipped guard.
- **Strictly-necessary-input rule** (document explicitly in the skill): stop and ask only for (a) failing tests/lint that the agent cannot fix within the issue''s scope, (b) refused merges/non-fast-forward pulls, (c) ambiguous or contradictory issue specs, (d) any action outside the confirmed queue. Everything else proceeds.
- Default failure policy: **stop the cycle** on the first stop condition, report progress so far, leave the repo on the default branch, clean.
- Final batch report: per issue - PR URL, merge result, duration; queue items skipped/blocked.
- Cap: refuse queues longer than a documented max (e.g. 10) without an explicit `max:<n>` override.

## Acceptance criteria

- Template-contract tests: consolidated confirm, stop-condition list, cap, batch report all asserted in the rendered skill.
- Docs (workflow doc + docs/cli.md pointer) + HISTORY.

## Out of scope

Resume-after-interruption and skip-and-continue policy (stage 2); parallel dispatch (stage 3).
