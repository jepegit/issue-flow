---
title: Split a big issue
---

# Split a big issue

## Goal

Cut **one existing** issue that is too big for a single PR into 2–5 linked
GitHub sub-issues, keeping the original open as the tracker.

## Steps

1. Run `iflow split <N>` (or `iflow split` on the issue's branch).
2. The agent drafts 2–5 child issues, each with the same light structure as
   `iflow issue` (context, spec, acceptance). If the pieces must happen in
   stages or depend on each other, it stops and recommends an
   [epic](epics.md) instead.
3. Confirm once. The agent creates the children and links them to the parent
   as GitHub **sub-issues** (falling back to a `## Sub-issues` task list on the
   parent if the API fails). The parent stays open.
4. If the parent was your focus issue, its local files are parked in
   `02-partly-solved-issues/`.
5. The agent asks whether to start the first child. Otherwise, work through
   them with `iflow pick` like any other issue.

## Split or epic?

| Use | When |
| --- | --- |
| `iflow split` | The pieces are independent and can land in any order |
| `iflow epic` | The work has stages or dependencies, or needs a plan first |

## Related

- [Command reference](../issue-workflow.md) — `/iflow-split`
- [Create and run epics](epics.md)
- [Write a good issue](write-an-issue.md)
