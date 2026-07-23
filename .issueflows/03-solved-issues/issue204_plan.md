# Plan — #204 Gate next epoch on clear queue

## Goal

`/iflow-auto` must not start stage `k+1` while stage `k` has open published
issues or open inter-epoch blockers (`epic-status` / queue).

## Approach

1. Add **Next-epoch gate** step after clear / accepted / no open work.
2. Design doc section; skill/command/docs; tests for gate wording.
3. When gate passes and a later stage exists, continue under overnight auth.

## Files

- `iflow_auto` skill/command, `advanced-auto-mode.md`, workflow, tests, HISTORY
