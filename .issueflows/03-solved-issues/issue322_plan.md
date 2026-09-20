# Plan: #322 workspace bootstrap next-command hint

## Goal

Print a copy-pasteable `bootstrap --yes --default <member>` line when
`--default` is required. Never silently pick a default.

## Approach

Propose first `scaffolded` member, else first git member. Classify-only prints
`next: issue-flow workspace bootstrap [DIR] --yes --default <name>`. `--yes`
without `--default` puts the same line in the error. Help: `--default` takes a
folder name.

## Files

- `src/issue_flow/agent.py` — propose + print/error
- `src/issue_flow/cli.py` — `--default` help
- `tests/test_cli.py` — dry-run next line; `--yes` error names proposed member

## Test

`uv run pytest tests/test_cli.py -k workspace_bootstrap`
