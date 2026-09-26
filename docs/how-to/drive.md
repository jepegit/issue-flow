---
title: Drive an epic hands-off
---

# Drive an epic hands-off

## Goal

Take **one existing GitHub issue** describing a large change and let the agent
run the whole epic path after a single confirmation: draft a staged plan,
publish every stage, work through each stage, review, and tidy up.

## Steps

1. Make sure the change is described in a GitHub issue `<N>`. If not, create
   one with `iflow issue epic <intent>`.
2. Optional: preview with `iflow drive <N> dry-run` (shows the plan state and
   queue; changes nothing).
3. Run `iflow drive <N>` and read the one confirmation carefully. It covers:
   - accepting the drafted plan (unless you add `grill` to be interviewed first);
   - publishing every stage as GitHub issues;
   - running each stage hands-off with [auto mode](auto-mode.md), which merges
     PRs and may reopen or create issues after its review. Issues the plan
     judged `yolo: no` are **not** a stop: they run on the cycle's non-yolo
     lane (same chain and safeguards) and land per the `cycle_nonyolo` policy
     — `merge` (default), `pr-only`, or `stop`. Override for one run with
     `nonyolo:<policy>`; the confirm lists which issues take that lane;
   - a final review that may create issues for anything left over;
   - deleting landed local branches: `git branch -d` for reachable ones and
     `git branch -D` for squash-landed ones (tip SHAs are printed; branches
     with unique work are never touched).
4. Let it run. It writes `drive_status.md` in `01-current-issues/` as it goes.
   It **pauses and asks** only when auto mode's review budget runs out, or when
   a stop condition trips (failing tests, a merge refused for something the
   sync cannot resolve, an ambiguous spec). A PR that turns out to be already
   merged, or a conflict in `HISTORY.md` / a design guide / a status file, is
   handled on the spot.
5. To stop early, send `stop` (or `abort`, `cancel`, `halt`). It stops at the
   next issue or stage boundary and leaves the default branch clean.
6. At the end it prints `iflow status`. Landed branches are already gone; run
   `iflow cleanup` only if you want the GitHub remote audit too.

"Never rebase / force-push" in the drive's rules is about the **default
branch**. Issue branches are rebased onto `origin/<default>` and pushed with
`--force-with-lease` by `issue-flow agent sync-branch` as part of every close —
that is expected, not a violation.

If the plan already exists and is confirmed, the drive skips drafting and
publishing and goes straight to running the stages.

## Related

- [Create and run epics](epics.md) — the same path, step by step
- [Use auto mode](auto-mode.md) — one stage at a time
- [Command reference](../issue-workflow.md) — `/iflow-drive`
