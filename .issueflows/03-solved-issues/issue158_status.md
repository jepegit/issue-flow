# Issue #158 — status

- [x] Done

## What's done

- `issue-flow workspace update` — discovers registry, runs `run_update` per member
- CLI wired under `workspace` typer (`--skip-dep-check`, `--editor`, `--json`)
- JSON mode suppresses per-member Rich noise; partial failures continue
- Tests: happy path, no registry, partial failure, help listing
- `multi-repo-workspaces.md` documents batch update
- PR #159 opened; 466 tests pass

## Remaining work

- None
