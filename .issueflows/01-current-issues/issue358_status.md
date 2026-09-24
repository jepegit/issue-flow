# Status — Issue #358

- [ ] Done

## What's done (PR 1 — template restructure)

- `docs/issue-workflow.md.j2` rewritten as **"issue-flow command reference"**:
  - an intro naming the project's editor, with links to Editor support and Concepts;
  - the workspace paragraph cut to 2 lines plus a how-to link (the missing details moved to `docs/how-to/workspaces.md`);
  - **one** command table (Command · What it does · Path · Modes), grouped Core loop / Starting work / Hands-off and special runs / Helpers / Maintenance;
  - one H3 per command with When to use · Arguments · What it does · What it asks you · Result · Related;
  - changelog wording removed.
- Every conditional kept (`worktree_first`, `auto_switchback`, `remind_cleanup`, `defer_changelog`, `confirm_changelog_update`, `fix_auto_name`, `step_directives`, `label_flows`, mode note).
- **New:** a `/iflow-pr-sync` section. It is a scaffolded command the old doc never documented; the new per-command test caught it. A new `/iflow-doctor` section was also added (it was only in the table before).
- `modes.command_mode_membership()` and the `command_modes` render-context key drive the Modes column. In non-standard modes, missing commands are marked "*not installed here*" but still documented.
- Tests: `tests/test_workflow_doc.py`, with a structure check for each of cursor / claude / opencode / codex, a Modes column vs `modes.toml` check, the novice marking, and a membership check (essential). `test_config.py` expects the new context key.
- Verified by rendering 5 throwaway projects (4 editors + novice). All 869 tests pass. Link check: internal and external both 0 errors.

## Remaining work

- PR 2: rename the "[The workflow]" link texts across `docs/` and `llms.txt` to "Command reference".
