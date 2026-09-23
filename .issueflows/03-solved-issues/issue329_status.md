# Status: #329 worktree_first knob

- [x] Done

## What's done

- Plan accepted (`worktree_first` default on; tokens win; no novice seed).
- Knob wired: `DEFAULT_WORKTREE_FIRST = true`, `Settings.resolve_worktree_first`, `modes.read_worktree_first`, `config_ops`, default `config.toml` comment, `issue-flow config` help.
- `_worktree_start.md.j2` gated: on → worktree-add unless `inplace` / `no worktree`; off → `git switch -c` on home unless token `worktree`.
- Command twins: `iflow-pick` / `iflow-issue` / `iflow-fix`.
- Docs: `worktrees.md`, `configuration.md`, `skill-behaviour-knobs.md`, `separate-workspaces.md`, workflow one-liner.
- This repo's `config.toml` left unset (default on).
- Tests: default true; config flip; pick skill/command footer wording both ways.
- `uv run ruff check src/ tests/` pass. Full `uv run pytest`: 834 passed.
- HISTORY.md bullet under `[Unreleased]`.

## Remaining work

- None. Close: commit, push, PR.
