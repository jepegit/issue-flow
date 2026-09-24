# Plan — Issue #363: docs: add an annotated sample session

(Started directly at the user's request ("go ahead directly"), skipping the pick survey and the plan-approval stop. The spec was already detailed, and the source material is a recorded real session.)

## Goal

A published page shows one full issue from pick to cleanup, with an example plan file and the confirmation points labelled. It is linked from Getting started.

## Approach

- Source: the raw log recorded while #328 was worked through normally in Claude Code (pick → plan → Accept → build → close → cleanup, 2026-09-24), plus the real `03-solved-issues/issue328_plan.md`. Trim, never rewrite output. Paths are shortened to `<tmp>` / `…`.
- New `docs/how-to/sample-session.md`, with a section per step: what you type, what the agent did and printed, and a `!!! question "Confirmation point"` admonition wherever it stopped. Includes the first cleanup that refused because the PR was not merged.
- Excerpt of the real plan (Goal, the location table, the open questions).
- Caveats up front: the transcript is from Claude Code, and the worktree path at the start is the behaviour before #328.
- Nav: How-to guides → Everyday (first entry after "Work one issue end-to-end"). Links from Getting started (step 4 and Where to go next) and the How-to index.

## Test strategy

Build, link check, pytest.
