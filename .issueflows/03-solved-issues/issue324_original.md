# Issue #324: Opt-in: sync *.code-workspace folders with workspace members

Source: https://github.com/jepegit/issue-flow/issues/324

## Original issue text

### Problem / context

`issue-flow workspace bootstrap` / `init` write `issueflow-workspace.toml` only. They do not update a sibling VS Code / Cursor multi-root file (e.g. `cellpy.code-workspace`). After cloning `cellpy-simple-gui`, it was missing from both the stale toml (#323) and `cellpy.code-workspace`.

Today that is intentional: issue-flow does not own editor workspace files. Generating `.code-workspace` per worktree was deferred in `separate-workspaces.md`. A **parent-folder** multi-root file is a different, optional convenience.

### Spec

1. Opt-in flag, e.g. `issue-flow workspace init|bootstrap --code-workspace [PATH]`.
   - Default path when the flag is bare: the single `*.code-workspace` in the workspace root, or `<folder-name>.code-workspace` if none exists.
   - Two or more `*.code-workspace` files and no path → refuse and list them.
2. Sync **folder entries** to current toml/classify members (relative paths). Do not rewrite unrelated `settings` / `extensions` / `launch`. Add missing member folders; do not delete folders the user added that are not members unless `--force` (document that).
3. Off by default. No `--yes` implied.
4. Docs: how-to/workspaces + CLI help. Not part of `iflow-init` auto-`--yes` unless we add an explicit confirm later.

### Acceptance criteria

- Without the flag, no `*.code-workspace` is created or edited.
- With the flag, a new member appears as a `folders[].path` entry; existing settings keys survive.
- Ambiguous multiple workspace files: exit 1, no write.

### Out of scope

- Auto-opening the workspace (`agent open-workspace` already print-only).
- Per-issue worktree `.code-workspace` files (still deferred).
- #322 / #323 CLI copy; implement those first so member lists are correct before sync.
