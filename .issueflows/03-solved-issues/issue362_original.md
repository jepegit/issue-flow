# Issue #362: docs: add how-tos for fix, issue, split, ops and drive

Source: https://github.com/jepegit/issue-flow/issues/362

## Original issue text

## Context and spec

Final-review finding for epic #341 (acceptance criterion "missing how-tos"; review §10). Five off-path commands have no how-to page: `/iflow-fix`, `/iflow-issue`, `/iflow-split`, `/iflow-ops`, `/iflow-drive`.

Add a short page for each, in the existing **Goal → Steps → Related** format (see `how-to/yolo.md`):

- `how-to/fix-session.md` (iterative small fixes);
- `how-to/write-an-issue.md` (`iflow issue`, including `epic` anchors);
- `how-to/split-an-issue.md`;
- `how-to/ops.md` (no-PR work);
- `how-to/drive.md` (compose epic → publish → auto).

Add them to the nav groups (Faster: fix; Bigger changes: issue, split, drive; Team and repos: ops) and to the How-to index tables.

**Goal:** five new pages in the nav and the How-to index, each stating when to use the command, with the steps and the confirmation points. The docs link check passes.

**Model:** deep

Depends on: #348

Part of epic #341.
