# Issue #243: `/iflow-cleanup` cannot prune squash-merged branches (`-d` vs `git cherry`)

Source: https://github.com/jepegit/issue-flow/issues/243

## Original issue text

## Problem / context

`/iflow-cleanup` step 4 promises to delete "every local branch whose tip is already reachable from `origin/<default>` (include squash-merges via `git cherry`)" using `git branch -d`, and forbids `-D`.

Those rules are mutually exclusive. `git cherry` proves **patch equivalence**; `git branch -d` requires **reachability**. This repo squash-merges (`pr_merge_method = "squash"`), and a squash-merged branch tip is never an ancestor of the default branch — so `-d` always refuses and cleanup can never prune anything. Stale branches accumulate silently while the command reports success.

Observed 2026-09-04 right after #242 merged: all 15 local branches were squash-merged, `git branch --merged main` was **empty**, and 14 of them were provably landed (merged PR for the head, or every commit patch-equivalent to `main`). They had to be deleted by hand with `-D` — exactly the operation the skill forbids. Branches had been piling up since #125.

## Spec

Teach cleanup about the squash case instead of pretending `-d` covers it:

- **Classify** each local branch:
  - `reachable` — ancestor of `origin/<default>`; `-d` works today.
  - `squash_landed` — not reachable, but `git cherry origin/<default> <branch>` reports no unique commits, **or** `gh pr list --head <branch>` shows a merged PR.
  - `unique_work` — anything else.
  - `skipped` — current branch, default branch, protected.
- **Deletion policy:** `reachable` → `-d` as today. `squash_landed` → `-D` allowed **only** behind a dedicated confirm, separate from the Phase A yes, that lists each branch with its tip SHA (recoverable via `git branch <name> <sha>`). `unique_work` → never deleted, even on confirm.
- **Always print tip SHAs before deleting** so every delete is recoverable.
- Consider a deterministic helper, `issue-flow agent local-branches --json`, mirroring `agent branches` (which today audits only *remote* branches).
- **Fix the false claims** in the `iflow_cleanup` skill + command templates, the branch-hygiene bullet in `rules/_body.md.j2`, and the cleanup section of `docs/issue-workflow.md.j2`.

## Acceptance criteria

- Classification distinguishes `reachable` / `squash_landed` / `unique_work`, covered by tests on a temp repo containing a real squash merge.
- `/iflow-cleanup` deletes `squash_landed` branches only after a dedicated confirm listing names + tip SHAs; declining leaves every branch in place.
- A branch with unique commits is never deleted, with or without the confirm.
- Docs no longer claim `-d` handles squash merges.
- If the CLI helper lands: `--json` payload is test-covered and the templates prefer it with a manual `git`/`gh` fallback.

## Out of scope

- Remote branch deletion — already Phase B / `agent branches`.
- Changing `pr_merge_method`, or asking projects to stop squash-merging.
