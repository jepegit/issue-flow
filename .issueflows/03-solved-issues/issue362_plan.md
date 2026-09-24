# Plan — Issue #362: docs: add how-tos for fix, issue, split, ops and drive

(Epic #341 stage 4, via /iflow-drive run 2 → auto → cycle; yolo chain, auto-confirmed.)

## Goal

Five new pages in the nav and the How-to index. Each says when to use the command, gives the steps, and marks the confirmation points. The link check passes.

## Approach

- Goal → Steps → Related pages, in the format of `how-to/yolo.md`: `fix-session.md`, `write-an-issue.md`, `split-an-issue.md` (with a split-vs-epic table), `ops.md`, `drive.md`.
- Content comes from the command reference sections (verified for #358).
- Nav: fix → Faster; drive / issue / split → Bigger changes; ops → Team and repos. The How-to index tables follow the same grouping.
- Also point the command reference's **Related** lines for these five commands at the new pages (template change + re-render).

## Test strategy

Build, link check, pytest.
