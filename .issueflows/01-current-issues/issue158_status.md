# Issue #158 — status

- [ ] Done

## What's done

- `issue-flow workspace update` — discovers registry, runs `run_update` per member
- CLI wired under `workspace` typer (`--skip-dep-check`, `--editor`, `--json`)
- JSON mode suppresses per-member Rich noise; partial failures continue
- Tests: happy path, no registry, partial failure, help listing
- `multi-repo-workspaces.md` documents batch update

## Remaining work

- `/iflow-close` — full test run already green locally
