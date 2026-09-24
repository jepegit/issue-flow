# Plan — Issue #348: docs: slim the home page and unify the quick start

(Epic #341 stage 2, via /iflow-drive → /iflow-auto → /iflow-cycle; yolo chain, auto-confirmed. Model: deep; planned as yolo: no because the wording is a judgement call. Please review the tone after merge.)

## Goal

The home page is about one screen plus the entry points, and Home, Getting started and README show the same quick start.

## Approach

- Rewrite `docs/index.md` with these parts:
  - a concrete benefit statement, keeping the author's "maybe that is a good thing" line in a softer form;
  - "How it works" with the canonical 5-row `iflow pick → … → cleanup` table (copied verbatim from Getting started);
  - three grid cards (New → Getting started, Specific task → How-to, AI agent → For agents / llms.txt), plus a Concepts pointer;
  - a 3-line install;
  - the license.
- Drop from Home: the Cursor-only file tree (Concepts and Editor support cover it), the long off-path list, the recipes (moved to the How-to index "Quick recipes"), and "Where to go next" (the tabs cover it).
- README: the Quick start uses the same table, replacing the `/iflow-capture 42` list. The "Why use it" text is replaced with the same benefit statement.
- New test `tests/test_doc_quickstart.py`: the table rows must be identical in all three files.

## Test strategy

Build (check the grid cards and icons render), link check, pytest.
