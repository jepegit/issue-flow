# Changelog conflicts — sync before merge, keep both bullets

**Issue:** [#240 — Changelog conflicts](https://github.com/jepegit/issue-flow/issues/240)
**Status:** decided 2026-09-04, implemented in the same issue.

## Context

`/iflow-close` synced with `git pull --ff-only` **on the issue branch**, which
only follows that branch's own upstream — it can never pick up commits that
landed on the *default* branch while the issue was in flight. The collision
therefore surfaced late, at merge time, as `mergeable: CONFLICTING` /
`mergeStateStatus: DIRTY`.

The reported case (a **sequential** `/iflow-cycle yolo` on `jepegit/cellpy`,
queue `#961 → #962 → #963`) shows why this is not just a parallel-dispatch
problem: an unrelated PR merged to `master` during #961's ~8 minute
test/implement/test window, and the only conflict was two additive bullets
under `## [Unreleased]`. Cycle step 6b treated the refused merge as a stop, so
`onfail:stop` halted the batch and #962 / #963 were never reached.

Sequential mode's "shared files stay single-writer" property holds *inside* the
cycle, but says nothing about the default branch moving externally.

## Decisions

1. **Sync explicitly, before push and again on a conflicted merge.** Close
   step 6 replays the issue branch onto `origin/<default>`; step 8a retries a
   `CONFLICTING` merge once after re-syncing.
2. **Rebase, not merge.** Keeps history linear and matches the manual
   precedent in the issue. The cost is that close must push with
   `--force-with-lease` (issue branch only — the default branch is never
   rewritten). `--strategy merge` exists for projects that would rather have a
   merge commit than a force-push.
3. **Auto-resolve only the mechanical shape.** All of: the changelog is the
   **only** conflicted file, every conflict region sits under
   `## [Unreleased]`, and both sides contain only list items. Then keep **all**
   bullets. Anything else — code conflict, edited or deleted bullet, renamed
   heading, promoted version section — aborts and stops.
4. **Ordering: the in-flight bullet goes last.** Already-landed bullets keep
   their positions. This matches `iflow-history-update` mode A's append
   semantics, so a resolved conflict is indistinguishable from having written
   the bullet after the other one landed. Note this is the **opposite** of the
   manual resolve in the issue report (which put ours first); the issue asked
   for one documented order, and consistency with mode A won.
5. **No config knob.** The behaviour is always on. Its "off" state is a known
   dead end (a halted batch over bookkeeping), so a knob would only add
   plumbing.
6. **One command, not two.** `issue-flow agent sync-branch` owns the git side;
   the pure text resolver lives in `issue_flow.history` for tests and reuse. A
   separate `agent history-resolve` was floated in the issue but has no second
   caller — the parallel coordinator *appends* bullets rather than resolving
   markers, and it can call `sync-branch` when a worker PR does go dirty.
7. **Never paper over a blocked merge.** No `gh pr merge --admin`, no skipping
   checks. A rebased branch needs a fresh check run, so watch-then-merge (with
   `--auto` as last resort) stays as it was.
8. **The CLI never pushes.** A rebase rewrites the branch, so the
   force-with-lease push stays in `/iflow-close`, inside the user's token and
   confirmation surface.

## Implementation

- `src/issue_flow/history.py` — conflict-marker parsing and the keep-both
  resolver, pure text in / text out, with explicit refusal reasons
  (`not_unreleased_section`, `heading_conflict`, `non_bullet_content`,
  `empty_side`, `unterminated_conflict`).
- `issue-flow agent sync-branch [--strategy rebase|merge] [--json]` in
  `agent.py` / `cli.py`, plus rebase/merge/unmerged-path helpers in
  `gitutils.py`. An abort **rolls back** any resolve made earlier in the same
  run, and the payload stops claiming `changelog_resolved` accordingly.
- Templates: `iflow_close` (step 6 sync + step 8a retry), `iflow_history_update`
  (the documented keep-both rule), `iflow_cycle` (step 6b is no longer tripped
  by a changelog-only refusal), `iflow_yolo`, and the mirrored command files.

## Links

Issue #240; timing rules in [changelog-timing.md](./changelog-timing.md);
parallel coordinator in [parallel-cycle.md](./parallel-cycle.md).
