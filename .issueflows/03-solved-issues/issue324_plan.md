# Plan: #324 opt-in *.code-workspace sync

## Goal

Optional `--code-workspace` adds member folders to a VS Code/Cursor
multi-root file. Off by default. Never delete extra folders unless `--force`.

## Approach

`--code-workspace` plus optional `--code-workspace-path`. Auto path: sole
`*.code-workspace`, else `<workspace-dir-name>.code-workspace`. Two files
and no path → exit 1, no JSON write. Merge `folders` only; keep `settings`.

## Files

- `src/issue_flow/project.py` — resolve + sync helpers
- `src/issue_flow/agent.py` / `cli.py` — init + bootstrap flags
- `docs/how-to/workspaces.md`
- `tests/test_cli.py`

## Test

No flag → no file. Flag → create with members. Existing settings survive.
Two `*.code-workspace` without path → exit 1.
