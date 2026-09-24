# Plan — Issue #364: agent queue — closed deps outside the queue block items; blocking not transitive

(Prerequisite yolo inside /iflow-drive 341 run 2; auto-confirmed.)

## Goal

Closed dependencies outside the queue satisfy dependencies, and a dependant of a blocked item is itself blocked.

## Approach

- `queueplan.build_queue(items, closed_external=frozenset())`: merge `closed_external` into `closed`. Compute blocked items to a fixed point (outside open deps first, then any item depending on a blocked member). `runnable` = members not blocked. The `blocked` tuples name the unmet deps, which are outside open deps or blocked in-queue members.
- `agent.run_queue`: collect the `depends_on` numbers that aren't in the queue, call `gh_issue_state` for each, and pass the closed ones. An unknown state stays open (conservative).
- Tests: 3 unit tests (two marked essential) and 1 CLI test.

## Test strategy

`uv run pytest`. Live check: `agent queue 358 359` (both depend on the closed #348). Old code → blocked [358, 359]; new code → queue [358, 359].
