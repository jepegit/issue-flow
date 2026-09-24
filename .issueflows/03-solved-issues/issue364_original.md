# Issue #364: agent queue: closed dependencies outside the queue block items, and blocking is not transitive

Source: https://github.com/jepegit/issue-flow/issues/364

## Original issue text

## Problem

Found while running `/iflow-drive 341`: `issue-flow agent queue --epic 341` (and `agent queue 346 347 348`) reported **#346 as blocked by #344**, even though #344 was already **CLOSED** (merged in Stage 1). It also queued **#347 before #346**, although #347 `Depends on: #346`.

```text
queue:   [347, 348]
blocked: [{number: 346, open_external_deps: [344]}]
```

Because of this, every epic stage after the first looks blocked by the previous stage's issues, and `/iflow-cycle epic <N>` / `/iflow-auto` would run stage issues in the wrong order.

## Cause

`queueplan.build_queue` (`src/issue_flow/queueplan.py`) has two faults:

1. **Closed deps outside the queue count as open.** `closed` only holds numbers of queue items whose `state == "closed"`. A dependency that is not a queue member (e.g. an issue from the previous stage) is never in `closed`, so `dep not in closed and dep not in members` marks it as an open external blocker. The caller (`agent.py`, `agent queue`) knows issue states (`gitutils.gh_issue_state`) but never looks up the state of deps outside the queue.
2. **No transitive blocking.** Once #346 is set aside as blocked, #347 (which depends on #346) stays runnable. Its only dep isn't in `runnable`, so Kahn gives it indegree 0 and #347 is queued ahead of its unmet dependency.

## Spec

- In `agent queue`, collect the `depends_on` numbers that aren't queue members, look up their state (`gh_issue_state`), and pass the closed ones into `build_queue` (e.g. a `closed_external: set[int]` parameter). Treat an `unknown` state as open (conservative).
- In `build_queue`, block transitively: an item whose dependency is blocked is itself blocked, and the blocked entry names the chain.
- Tests in `tests/test_queueplan.py`: (a) a closed dependency outside the queue doesn't block; (b) an open dependency outside the queue still blocks; (c) a dependant of a blocked item is blocked, not queued.

**Goal:** for epic #341 as it stood before Stage 2 ran (Stage 1 closed; #346 → #347 → #348 open), `agent queue --epic 341` returns queue `[346, 347, 348]` with `blocked: []`. The three new tests pass.

**Model:** default

Depends on: none

Recorded in `.issueflows/01-current-issues/auto_status.md` during the #341 drive.
