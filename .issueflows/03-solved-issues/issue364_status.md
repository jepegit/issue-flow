# Status — Issue #364

- [x] Done

## What's done

- `build_queue` takes `closed_external` and blocks transitively. The docstring rules are updated.
- `agent queue` looks up the state of dependencies outside the queue and treats closed ones as satisfied.
- New tests: `test_build_queue_closed_external_dependency_does_not_block` (essential), `test_build_queue_open_external_dependency_still_blocks`, `test_build_queue_blocking_is_transitive` (essential), `test_agent_queue_closed_dependency_outside_queue_is_satisfied`. Registry rows added.
- Live check: old code → queue [] / blocked [358, 359]; fixed code → queue [358, 359] / blocked []. Full suite: 862 passed.

## Remaining work

- None.
