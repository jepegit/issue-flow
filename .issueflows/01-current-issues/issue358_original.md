# Issue #358: docs: restructure the command reference and make it editor-neutral

Source: https://github.com/jepegit/issue-flow/issues/358

## Original issue text

## Context and spec

Final-review finding for epic #341 (goal part 4; review §6). The page the nav now calls **Commands** is the Cursor render of `src/issue_flow/templates/docs/issue-workflow.md.j2`. On the site this causes several problems:

- the H1 is "Cursor issue workflow (Agent Skills)";
- sections are numbered `0a, 0, 1, 1a … 8b, 10a`;
- the same ~25 commands are listed in two tables;
- a 400-word workspace paragraph sits in the intro;
- some wording reads like a changelog ("no planning step of its own any more", issue numbers);
- 12 links across `docs/` still call it "The workflow".

Change the **template** and re-render (`uv run scripts/update_issueflow_setup.py`):

- Use an editor-neutral title such as "Command reference". Keep the editor name only where paths differ, or use `pymdownx.tabbed` tabs per editor.
- Drop the numbering. Group the commands under Core loop / Starting work / Helpers / Automation / Maintenance.
- Keep one table: command · purpose · on/off path · modes that include it.
- Give every command section the same layout: When to use · Arguments · What it does · What it asks you · Result · Related how-to.
- Move the workspace paragraph to `how-to/workspaces.md`, and remove the changelog wording.
- Update the "The workflow" link texts across `docs/` to the new name.

This may be split into two PRs (template restructure, then link texts and site-specific tweaks).

**Goal:** the site's command reference has an editor-neutral H1, no numbered sections, a single command table, and the same section layout for every command. `grep -rn 'The workflow\](' docs` returns nothing. Template tests pass for every editor.

**Model:** deep

Depends on: #348

Part of epic #341.
