# Plan — Issue #347: docs: add a Concepts page with glossary

(Epic #341 stage 2, via /iflow-drive → /iflow-auto → /iflow-cycle; yolo chain, auto-confirmed. Model: deep. Content written from the current docs: workflow, configuration, editors, how-tos.)

## Goal

Every term listed in the spec is defined on one page, and Home, Getting started and the How-to index link to it.

## Approach

- New `docs/concepts.md` with these sections:
  - commands and skills, and the three ways to type a command;
  - the lifecycle, with a table of what each step writes, plus the dispatcher decision table;
  - the `.issueflows/` layout and group moves 01 → 02/03 (pause, close, sweep);
  - on-path vs off-path commands;
  - where the agent always stops to ask;
  - a glossary of 19 terms.
- Nav: replace the #346 comment with `Concepts`, between Getting started and How-to.
- Links: Home (after the command list, and in Where to go next), Getting started (step 4, and in Where to go next), How-to index intro.
- The site-wide glossary tooltips (`abbr` + snippets) were optional in the spec. Skipped: the page anchors are enough for now.

## Test strategy

Build, link check, pytest.
