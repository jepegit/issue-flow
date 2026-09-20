# Plan: #323 bootstrap --yes refreshes existing toml members

## Goal

`--yes` rewrites `members` from the current classify so a new clone is not
left out. Classify reports names on disk but missing from the toml.

## Approach

On `--yes`, always call `run_workspace_init` with `force=True` (refresh).
Keep file `default` only if `--default` omitted (single-member path).
Classify-only / `--yes` JSON: `missing_from_toml`. Drop silent dim `kept`.
Docs: how-to + `--yes` help.

## Files

- `src/issue_flow/agent.py`
- `src/issue_flow/cli.py`
- `docs/how-to/workspaces.md`
- `tests/test_cli.py`

## Test

Existing toml without sibling + new scaffolded child + `--yes --default` →
sibling in `members`. Classify JSON lists it in `missing_from_toml`.
