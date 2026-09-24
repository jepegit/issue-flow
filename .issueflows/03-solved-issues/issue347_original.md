# Issue #347: docs: add a Concepts page with glossary

Source: https://github.com/jepegit/issue-flow/issues/347

## Original issue text

## Context and spec

Create `docs/concepts.md` covering: the lifecycle (capture → plan → build → close → cleanup) and the file each step writes; the `.issueflows/` layout and how issue groups move between 01/02/03 (move the file tree here from the home page); on-path vs off-path commands; where the agent always stops to ask; and a glossary table (focus issue, off-path, dispatcher, parked, sweep, yolo, epic, stage, epoch, adversarial review, squash-landed, mode vs skill level vs noob, managed block, harness, worktree-first). Explain once that "command" and "skill" refer to the same thing depending on the editor. Optionally add glossary tooltips site-wide via `abbr` + snippets. See review §5, §13.

**Goal:** every term above is defined on one page, and the other pages link to it at first use on Home, Getting started, and the How-to index.

**Model:** deep

Depends on: #346

Full review: `.issueflows/04-designs-and-guides/docs-usability-review.md`.

Part of epic #341.
