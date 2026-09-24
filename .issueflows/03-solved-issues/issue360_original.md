# Issue #360: docs: add a troubleshooting page

Source: https://github.com/jepegit/issue-flow/issues/360

## Original issue text

## Context and spec

Final-review finding for epic #341 (acceptance criterion "troubleshooting page"; review §8). Common first-hour failures are not collected anywhere.

Add `docs/how-to/troubleshooting.md` with **symptom → cause → fix** entries, at least:

- `gh` not authenticated;
- `issue-flow` not on PATH after `uv tool install`;
- skills missing from the slash menu (restart the editor; wrong `--editor`);
- stale skills (the `issue-flow-version` stamp doesn't match `issue-flow --version` → `issue-flow update`);
- a local branch "several commits ahead" after a squash merge (→ `iflow cleanup`);
- leftovers in `01-current-issues/` (→ `iflow doctor`);
- `git pull --ff-only` refused on the default branch (→ `issue-flow agent default-sync`);
- WSL vs native Windows config paths.

Link it from Getting started, the How-to index, and Concepts. Add it to the nav under How-to guides.

**Goal:** the page exists in the nav, covers the listed symptoms, is linked from those three pages, and the docs link check passes.

**Model:** deep

Depends on: #348

Part of epic #341.
