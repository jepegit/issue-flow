# Plan — Issue #358: docs: restructure the command reference and make it editor-neutral

Epic #341, Stage 3. Stopped the hands-off run (not yolo-sized). Planned interactively.

## Goal

Every editor's render of the workflow doc becomes a scannable **command reference**:
- an editor-neutral title;
- commands grouped by purpose;
- one command table;
- the same section layout for every command.

The docs site stops calling it "The workflow".

## Constraints

- **Change the template, not the render.** Edit `src/issue_flow/templates/docs/issue-workflow.md.j2`, then re-render with `uv run scripts/update_issueflow_setup.py`.
- **Every project gets this page.** It is written into every scaffolded project as `docs/issue-workflow.md`, and `issue-flow update` overwrites it there. So it must still read well inside a project, for its one editor, not only on the site. Paths such as `{{ agent_dir }}/skills/…` stay rendered for that project's editor.
- **Keep all knob-dependent wording.** The template has 53 conditionals (`commands_supported`, `worktree_first`, `auto_switchback`, `remind_cleanup`, `defer_changelog`, `confirm_changelog_update`, `fix_auto_name`, `step_directives`, `mode`, `included_skills`). Their wording is kept; only where it sits changes.
- **Keep the tested content.** About 11 tests check for content, not layout. Examples: "Keyboard-friendly chat" comes before slash forms; `` `iflow plan`, `iflow-plan`, `/iflow-plan` ``; `second, dedicated confirm`; `drive-mode.md`; `label:<L>`; `iflow review yolo`; `iflow epic start`. Keep that content. Change a test only where the wording legitimately changes, and say so in the PR.
- **Keep the output path.** The file stays at `docs/issue-workflow.md`, so the site URL `/issue-workflow/` is unchanged.

### Prior art

- `docs/concepts.md` (#347) already explains the lifecycle, on-path vs off-path, and invocation forms. The reference should link to it rather than repeat it.
- `modes.toml` / `modes.py` define which commands each mode installs. `included_skills` in the render context covers only the **current** mode.
- `.issueflows/04-designs-and-guides/docs-link-check.md` covers link rules: versioned RTD URLs, GitHub URLs for design notes.

## Approach

**PR 1 — template restructure**

1. **Title and intro.** H1 becomes `# issue-flow command reference`. It is followed by one line: "This project uses **{{ editor_name }}**: commands are {skills under `{{ agent_dir }}/skills/` | slash commands under …}. Paths below are for {{ editor_name }}; other editors: [Editor support](RTD link)." The intro keeps:
   - the keyboard-friendly chat block;
   - the "type `iflow`" pointer;
   - the setup pointer;
   - a link to Concepts on the site.
2. **Workspace paragraph.** The 400-word multi-root paragraph shrinks to 2 lines plus a link to `how-to/workspaces/` on the site. Its unique content moves into `docs/how-to/workspaces.md`: the worktree tokens, `default-sync`, `open-workspace`.
3. **One command table.** Merge the "entry points" and "Agent Skills" tables into one: **Command · What it does · Path · Modes**.
   - The **Path** column shows on/off path.
   - The **Modes** column comes from a new render-context value, `command_modes`, computed in `templating.py` from `modes.toml` (for example `standard, novice`).
   - The invocation forms (`` `iflow plan`, `iflow-plan`, `/iflow-plan` ``) are explained once above the table, not repeated per row.
   - The helper-skills rows (`iflow-version-bump`, `iflow-history-update`) go in a small "Helper skills" note under the table.
4. **Groups instead of numbers.** Replace the `0a/0/1/1a … 8b/10a` headings with five H2 groups and one H3 per command:
   - **Core loop:** `iflow`, capture, plan, build, close, cleanup
   - **Starting work:** setup, init, pick, issue, split, epic
   - **Hands-off and special runs:** yolo, fix, ops, cycle, auto, drive
   - **Helpers:** pause, status, review
   - **Maintenance:** doctor, archive, graphify
5. **Same layout for every command:**

   ```text
   ### `/iflow-x` — short purpose
   **When to use** · **Arguments** · **What it does** (numbered) · **What it asks you** · **Result** · **Related** (how-to link)
   ```

   - "What you pass" becomes **Arguments**. The Off-path notes merge into the table and a single line.
   - **What it asks you** is new: one line listing the confirmation points each command already describes.
   - **Related** links to the matching how-to on RTD, where one exists.
6. **Wording cleanup.** Remove changelog wording: "no planning step of its own any more", "(issue #…)" in prose, "New …".
7. **Closing sections.** "Branch and folder hygiene" and "End-to-end flow" stay as the last two sections, unchanged except for headings.
8. **Tests.** Add a template test for each editor (cursor, claude, opencode, codex) and for novice mode. Each checks:
   - H1 = "issue-flow command reference";
   - no `## \d+a?\.` numbered headings;
   - exactly one command table;
   - every command has an H3 with the five labels.

   Also add a test that `command_modes` matches `modes.toml`.

**PR 2 — site link texts** (small)

9. Rename "[The workflow](…)" to "[Command reference](…)" across `docs/` (12 links) and `docs/llms.txt`. Update the Concepts and How-to index wording to match.

## Files to touch

- **PR 1:**
  - `src/issue_flow/templates/docs/issue-workflow.md.j2`: restructure
  - `src/issue_flow/templating.py`: add `command_modes` to the context
  - `docs/issue-workflow.md`: re-rendered
  - `docs/how-to/workspaces.md`: receives the workspace details
  - `tests/test_templating.py` and `tests/test_init.py`: new structure tests, plus tweaks where wording legitimately changes
  - `HISTORY.md`
- **PR 2:** `docs/*.md`, `docs/how-to/*.md`, `docs/llms.txt`.

## Test strategy

- `uv run pytest`, including the new per-editor and per-mode structure tests.
- `scripts/check_doc_links.sh`.
- Render once per editor into a temporary project and skim each output by eye.

## Open questions

1. **Modes column.** Compute it from `modes.toml` (a small `templating.py` change, can't drift), **or** drop the column and just mark commands missing from the current mode as "not installed here"? *Recommended: compute from `modes.toml`.*
2. **Commands not in the current mode.** Should a `novice` project's page still document all ~25 commands (marked "not installed in this mode"), or only the installed ones? *Recommended: document all, marked, so the page doubles as an upgrade guide. The site render (`standard`) is unaffected either way.*
3. **Two PRs or one?** *Recommended: two, as above. PR 1 is the risky template change; PR 2 is mechanical.*
4. **Group names.** Are the five groups in step 4 OK, in particular "Hands-off and special runs" for yolo / fix / ops / cycle / auto / drive?
