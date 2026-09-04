# Status — Issue #240: Changelog conflicts

- [x] Done

Branch: `240-changelog-conflicts`
Plan: [issue240_plan.md](./issue240_plan.md) — accepted 2026-09-04 (rebase strategy,
in-flight bullet last, no config knob, single `agent sync-branch` command).
Design record: [changelog-conflicts.md](../04-designs-and-guides/changelog-conflicts.md)

## What's done

Fully implemented; closed via `/iflow-close` on 2026-09-04.

- **`src/issue_flow/history.py`** (new) — conflict-marker parsing plus the
  keep-both resolver. Resolves only when the conflict is confined to
  `## [Unreleased]` and both sides are bullet-only; otherwise returns an
  explicit refusal reason (`not_unreleased_section`, `heading_conflict`,
  `non_bullet_content`, `empty_side`, `unterminated_conflict`). Preserves CRLF
  and trailing newlines.
- **`src/issue_flow/gitutils.py`** — added `repo_root`, `rebase_onto`,
  `rebase_continue`, `rebase_abort`, `rebase_in_progress`, `merge_ref`,
  `merge_abort`, `merge_continue`, `unmerged_paths`, `stage_paths`.
- **`issue-flow agent sync-branch [--strategy rebase|merge] [--json]`**
  (`agent.py` `run_sync_branch`, registered in `cli.py`) — refuses on a dirty
  tree / the default branch, fetches, rebases onto `origin/<default>`,
  auto-resolves a changelog-only conflict, aborts on anything else. Never
  pushes. An abort rolls back an earlier resolve in the same run and the
  payload stops reporting `changelog_resolved` (a bug the mixed-conflict test
  caught).
- **Templates** — close step 6 (sync) + step 7 (`--force-with-lease`) +
  step 8a.7 (retry once after a `CONFLICTING` refusal) + constraints;
  `iflow-history-update` gained the documented keep-both rule;
  `iflow-cycle` step 6b no longer stops on a changelog-only refusal, and its
  conflict-stance / parallel-coordinator sections were updated; `iflow-yolo`
  and the mirrored command templates follow.
- **Docs** — new design doc `changelog-conflicts.md`, cross-links from
  `changelog-timing.md` and `parallel-cycle.md`, `agent sync-branch` in
  `docs/cli.md`, close's steps in the workflow doc template, and a
  `HISTORY.md` `[Unreleased]` bullet.
- **Tests** — `tests/test_history.py` (16 resolver units incl. every refusal
  path) and `tests/test_agent_sync_branch.py` (9 integration cases on real
  temp git repos reproducing the reported cellpy scenario), plus three
  scaffold assertions in `tests/test_init.py`. Full suite: 632 passed;
  `ruff check` / `format` clean.

## Deviations from the issue report

- The comment's manual resolve put the in-flight bullet **first**; the shipped
  rule appends it **last**, for consistency with `iflow-history-update` mode A.
  Recorded in the design doc.
- No separate `agent history-resolve` command — the resolver is importable from
  `issue_flow.history` and has no second caller yet.

## Remaining work

None. Post-merge: run `/iflow-cleanup`.
