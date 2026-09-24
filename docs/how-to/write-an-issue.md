---
title: Write a good issue
---

# Write a good issue

## Goal

Turn an idea into **one well-specified GitHub issue** (context, spec,
acceptance criteria), and optionally start working on it straight away.

## Steps

1. Run `iflow issue <what you want>`, for example
   `iflow issue add a dry-run flag to doctor`. With no text, the agent asks for
   a one-line intent.
2. The agent drafts a title and a body with **Problem / context**, **Spec**,
   **Acceptance criteria**, and (optionally) **Out of scope**. Edit it together
   until it says what you mean.
3. Confirm the final text. The agent runs `gh issue create` and reports the
   new number `N`.
4. The agent asks whether to start now. On yes it creates the branch
   `<N>-<slug>` (in a sibling worktree by default), captures the issue, and
   asks before continuing to `iflow plan`. On no, pick it up later with
   `iflow pick`.

If the draft is clearly too big for one PR, the agent offers
[`iflow split`](split-an-issue.md) or an [epic](epics.md) instead of creating
children itself.

**Epic anchors:** `iflow issue epic <intent>` creates the umbrella issue for an
epic (`Epic:` title, plus the `epic` label when the repo has one). Then run
`iflow epic <N>`.

## Related

- [Command reference](../issue-workflow.md) — `/iflow-issue`
- [Work one issue end-to-end](work-one-issue.md)
- [Run a fix session](fix-session.md) — many small fixes instead of one deliverable
