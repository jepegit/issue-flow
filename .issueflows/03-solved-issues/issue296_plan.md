# Plan — #296 Dedupe workspace update and the registry

## Goal

`--workspace` union updates an overlapping root once; defaults stay two separate sets.

## Approach

Shared `unique_resolved_paths`. `update --all` stays registry-only.
`update --all --workspace` unions nearest `issueflow-workspace.toml`
members with registry roots. `workspace update` skips duplicate
resolved member paths. Docs + tests.

## Files

- `src/issue_flow/project.py`, `init.py`, `cli.py`, `agent.py`
- `docs/cli.md`, design docs, `HISTORY.md`

## Tests

Overlapping tmp root once in union; without `--workspace`, no workspace walk.
