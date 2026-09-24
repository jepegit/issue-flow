# Status — Issue #328

- [x] Done

## What's done

- New settings `worktrees_dir` (text, default `""`) and `worktrees_in_workspace` (bool, default `true`): `config_ops.CONFIG_KEYS`, `modes` readers and the `config add` writer, `Settings.resolve_*`, env fallbacks `ISSUEFLOW_WORKTREES_DIR` / `ISSUEFLOW_WORKTREES_IN_WORKSPACE`, and `config show`.
- `gitutils.resolve_worktree_location` → `WorktreeLocation(path, reason, note)`, with reasons `sibling` / `workspace` / `worktrees_dir` / `fallback`. It never creates the folder.
- `agent worktree-add` uses it; its JSON has `location` + `location_note`, and the text output shows the reason and any note. `agent worktree-remove <N>` uses the same resolver.
- Templates (`_worktree_start`, `iflow-cycle` parallel workers, command reference) no longer hard-code `../<repo>-<N>`. Re-rendered.
- Docs:
  - `configuration.md`: 2 rows in All settings, plus a Common changes row;
  - `how-to/worktrees.md`: "Where the worktree goes";
  - design note `separate-workspaces.md`.
- Tests: `tests/test_worktree_location.py` (10; 3 essential). Registry rows added. Full suite: 882 passed. Link check: 0 errors.
- Real run in an isolated HOME: `config set --global worktrees_dir ~/worktrees` → `worktree-add` created `~/worktrees/demo-6` (`worktrees_dir`); with the folder removed → `../demo-7` (`fallback`, with a note).

## Remaining work

- None.
