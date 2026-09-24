# Plan — Issue #328: location of worktrees

## Goal

Let users choose where issue worktrees go:

- **Repos inside a workspace folder** (a parent folder with `issueflow-workspace.toml`) keep today's behaviour: the worktree goes next to the repo, inside that folder.
- **Stand-alone repos** can use a **common worktrees folder** (e.g. `~/worktrees`) instead of cluttering the repo's parent folder.
- Anything unset or missing falls back to today's behaviour.

## Constraints

- **Default behaviour is unchanged.** Without the new settings, `worktree-add` still creates `../<repo>-<N>`.
- **Home is never switched.** Idempotency and `origin/<default>` as the start point stay as they are (#255 / #303 / #329).
- **Every worktree command must find a worktree wherever it lives.** That covers `worktree-remove`, cleanup and `open-workspace`. They mostly look worktrees up via `git worktree list`; the one path-based lookup (`worktree-remove <N>`) must use the same resolver.
- **New knobs follow the existing pattern:** `CONFIG_KEYS`, a `modes.read_*` reader, a `Settings.resolve_*` resolver, and an `ISSUEFLOW_*` env fallback. They are listed in `docs/configuration.md` (a test enforces this since #359).
- **A folder path is machine-specific,** so the docs recommend setting it user-wide (`config set --global`). Project config is still allowed.

### Prior art

- `gitutils.worktree_path_for_issue(home, N)` → `home.parent / f"{home.name}-{N}"`. It is the single source of the path and is used by `add_worktree` and `run_worktree_remove`.
- `project.find_workspace_file(start)` walks up to `issueflow-workspace.toml`. That is exactly the "repo is inside a workspace folder" check.
- `Settings.resolve_worktree_first` / `resolve_auto_remove_worktree` are the resolver pattern to copy.
- Templates that state the path: `skills/_worktree_start.md.j2`, `skills/iflow_cycle/SKILL.md.j2`, `docs/issue-workflow.md.j2` (4 mentions of `<repo>-<N>`).
- Design note `04-designs-and-guides/separate-workspaces.md` describes the sibling layout.

## Approach

1. **Two new settings** under `[issueflow]`:
   - `worktrees_dir`: text, default `""` (off). A common folder for issue worktrees. `~` and environment variables are expanded.
   - `worktrees_in_workspace`: bool, default `true`. When the repo is inside a workspace folder, keep the worktree next to the repo, in that folder.
2. **One resolver,** `gitutils.resolve_worktree_location(home, number, *, worktrees_dir, in_workspace) -> (path, reason)`, used by `worktree_path_for_issue`:

   | Situation | Worktree goes to | `reason` |
   | --- | --- | --- |
   | Repo inside a workspace and `worktrees_in_workspace = true` | `../<repo>-<N>` (in the workspace folder) | `workspace` |
   | `worktrees_dir` set, and the folder exists | `<worktrees_dir>/<repo>-<N>` | `worktrees_dir` |
   | `worktrees_dir` set but missing, or not absolute after expansion | `../<repo>-<N>` | `fallback: <why>` |
   | Nothing set | `../<repo>-<N>` | `sibling` |

   The resolver never creates the common folder (the issue says a missing folder means today's behaviour).
3. **`agent worktree-add`** resolves both settings for `home`, passes them through, and adds `location` (the reason) to its JSON payload. The text output says where the worktree went and why (e.g. "worktrees_dir /home/me/worktrees does not exist → sibling").
4. **`agent worktree-remove <N>`** computes the expected path with the same resolver (the branch-prefix match stays as a second route).
5. **Templates:** change the three that hard-code `../<repo>-<N>` to "the path `worktree-add` prints (by default `../<repo>-<N>`; see `worktrees_dir`)". Then re-render.
6. **Docs:**
   - `how-to/worktrees.md`: a "Where the worktree goes" section with the table above and a `config set --global worktrees_dir ~/worktrees` example.
   - `configuration.md`: two rows in All settings, and one Common changes row.
   - Update the `separate-workspaces.md` design note.

## Files to touch

- `src/issue_flow/gitutils.py`: resolver; `worktree_path_for_issue` / `add_worktree` take the location inputs.
- `src/issue_flow/agent.py`: `run_worktree_add` / `run_worktree_remove` resolve the settings; `location` in the payload.
- `src/issue_flow/config_ops.py`, `modes.py`, `config.py` (plus `config add` defaults): the two new keys, readers, resolvers, env fallbacks.
- `src/issue_flow/templates/skills/_worktree_start.md.j2`, `skills/iflow_cycle/SKILL.md.j2`, `docs/issue-workflow.md.j2`: path wording (re-render).
- `docs/how-to/worktrees.md`, `docs/configuration.md`, `.issueflows/04-designs-and-guides/separate-workspaces.md`.
- Tests: `tests/test_gitutils_worktree_location.py` (new, one test per table row, with real temp git repos); `tests/test_cli.py` (a `worktree-add` JSON `location` field); `tests/test_config.py` (the new keys).
- `HISTORY.md`.

## Test strategy

- `uv run pytest`, plus the new resolver tests: default sibling; inside a workspace; inside a workspace with `worktrees_in_workspace = false` and `worktrees_dir` set; `worktrees_dir` set and present; set but missing (fallback); relative path (fallback); `~` expansion.
- One end-to-end CLI test: `worktree-add` into a temp `worktrees_dir`, then `worktree-remove <N>` finds it.
- `scripts/check_doc_links.sh`.

## Open questions

1. **Names.** `worktrees_dir` + `worktrees_in_workspace`? Alternatives: `worktree_root` / `worktree_location`. *Recommended: the two above; they read well in `config show`.*
2. **Missing folder.** Fall back to the sibling path (as the issue says), or create the folder? *Recommended: fall back and print why. Creating directories from a config typo is worse than a visible fallback.*
3. **Relative paths.** A relative `worktrees_dir` is ambiguous (relative to what?). *Recommended: treat it as invalid → fall back with a note; accept absolute paths and `~`.*
4. **Folder name inside the common folder.** Keep `<repo>-<N>`, so two unrelated repos with the same name could collide (the existing "target path already exists" error then stops safely)? Or use `<owner>-<repo>-<N>`? *Recommended: keep `<repo>-<N>`, same as today, so the name doesn't depend on where the worktree is; the collision error is enough for now.*
