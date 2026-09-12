---
title: Park and resume
---

# Park and resume

## Goal

Stop mid-issue without abandoning tracking files, then pick the work up later.

## Steps

### Park

1. On the issue branch, run `iflow pause` (or `/iflow-pause`).
2. Agent updates `issue<N>_status.md`, moves the issue group to
   `.issueflows/02-partly-solved-issues/`, and may offer a WIP commit.
3. Home checkout can return to the default branch; leave the issue branch as-is
   until you resume.

### Resume

1. Run `iflow pick`. Parked groups are listed **first**.
2. Confirm the parked issue; capture/branch setup continues from there.
3. Type `iflow` to jump to the next linear step (usually plan or build).

Keep the status checkbox accurate (`- [ ] Done` while unfinished) so sweeps
route the group correctly.

## Related

- [The workflow](../issue-workflow.md) — `/iflow-pause`
- [Work one issue end-to-end](work-one-issue.md)
