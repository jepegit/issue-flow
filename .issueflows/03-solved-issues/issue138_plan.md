# Plan — Issue #138: deterministic `issue-flow agent epic-status` CLI

Part of epic #144, stage 2. Depends on #136 and #137 (stacked on the
137 branch — the plan-file format those slices defined is the parsing
contract here).

## Goal

`issue-flow agent epic-status <N> [-C DIR] [--local] [--json]` — read-only,
deterministic answer to "where does epic N stand?": stages, per-issue state
(published/unpublished, open/closed, blocked), the current stage, and the
next unblocked candidates.

## Approach

- New `src/issue_flow/epicplan.py`: parser for `epic<N>_plan.md`
  (`# Epic #<N>:` header, `Status:`, `## Stage <k> — <title>` sections,
  `### Issue:` specs with `Depends on:` / `yolo:` / `Published: #<M>`
  lines; `## Later (unstaged)` ignored). Reused by #140's `--epic` source.
- `gitutils.gh_issue_state(number)` — single-issue state lookup
  (`gh issue view <n> --json number,state`), graceful `None`.
- `agent.run_epic_status`: parse; unless `--local`, resolve each published
  number's state; derive per-spec `state` (`unpublished` / `open` /
  `closed` / `unknown`), `blocked_by` (deps not closed), stage `done`,
  `current_stage`, and `next_candidates` (current-stage, published, open,
  unblocked). Exit 1 when the plan file is missing.
- CLI command on the agent sub-app; fast-path note in the epic skill +
  command twin; docs/cli.md row; HISTORY; tests (parser unit fixtures +
  CLI with monkeypatched gitutils).
