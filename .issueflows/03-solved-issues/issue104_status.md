# Issue #104 status — Iterative small fixes

Interactive `/iflow-fix` session on branch `104-iterative-small-fixes`. Each confirmed fix is recorded as a dated bullet below; the session lands via `/iflow-close`.

- [x] Done

## Iterative fixes log

- **2026-07-02** — Added `--version` eager option to the root Typer callback in `src/issue_flow/cli.py` (prints `issue-flow <version>` via `importlib.metadata`); test `test_cli_version_option` added in `tests/test_cli.py`.
