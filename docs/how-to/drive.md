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
     PRs and may reopen or create issues after its review;
   - a final review that may create issues for anything left over;
   - deleting merged local branches with `git branch -d` only.
4. Let it run. It writes `drive_status.md` in `01-current-issues/` as it goes.
   It **pauses and asks** only when auto mode's review budget runs out, or when
   a stop condition trips (failing tests, a refused merge, an issue that turns
   out not to be small).
5. To stop early, send `stop` (or `abort`, `cancel`, `halt`). It stops at the
   next issue or stage boundary and leaves the default branch clean.
6. At the end it prints `iflow status`. Squash-merged branches are left for
   you: run `iflow cleanup` to remove them.

If the plan already exists and is confirmed, the drive skips drafting and
publishing and goes straight to running the stages.

## Related

- [Create and run epics](epics.md) — the same path, step by step
- [Use auto mode](auto-mode.md) — one stage at a time
- [Command reference](../issue-workflow.md) — `/iflow-drive`
