# Plan — Issue #140: deterministic `issue-flow agent queue` CLI

Part of epic #145 (cycling mode), stage 1. Stacked on the #138 branch (reuses
the `epicplan` parser for the `--epic` source).

## Goal

`issue-flow agent queue [N N ...] [--label L] [--epic N] [-C DIR] [--json]` —
read-only: resolve an issue set, parse `Depends on #N` / `Blocked by #N`
lines, topologically order the queue, flag blocked and independent issues.
Dependency cycles are reported (exit 1, naming the cycle), never silently
broken.

## Approach

- New `queueplan.py`: `parse_dependencies(body)` (dep-marker lines only, so
  prose `#N` refs don't count), `build_queue(items, closed)` — Kahn toposort
  restricted to in-queue deps, deterministic order; `blocked` = open deps
  outside the queue; `independent` = no dependency relation (either
  direction) to any other member; cycle detection.
- `gitutils`: `gh_issue_meta(number)` and `gh_issue_list_meta(label=…)`
  (number/title/state/body/labels).
- `agent.run_queue`: sources are mutually exclusive (exactly one required);
  explicit-number source refuses when any number can't be fetched (typo
  protection, like `agent archive`); closed issues are skipped and reported;
  `--epic` uses the current stage's published specs (yolo/deps from the
  plan, states via `gh_issue_state`), noting unpublished specs.
- CLI command, docs/cli.md, HISTORY, tests (unit + CLI with mocked gh).
