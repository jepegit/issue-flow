# Status for issue #18: better documentation on dependencies

- [x] Done

## Implementation summary

All items from `issue18_plan.md` have landed on branch
`18-better-documentation-on-dependencies`:

- **New module `src/issue_flow/dependencies.py`.** Declares
  `REQUIRED_DEPENDENCIES` (`git`, `gh`) with per-OS install hints and a
  docs link each. Exposes `check_dependencies()` (pure `shutil.which`)
  and `prompt_or_skip()` (prints the missing-deps report via `rich`,
  bypasses the prompt on `skip=True` or non-TTY stdin, otherwise calls
  `typer.confirm`). `uv` is deliberately not in the runtime check — it's
  only called out in the README as an install-time prerequisite.
- **Wired into `init.py`.** `run_init` and `run_update` now take a new
  `skip_dep_check` kwarg and call `_dependency_gate(skip_dep_check)`
  before doing any scaffolding. A decline at the prompt raises
  `typer.Exit(code=1)` so CI notices.
- **CLI surface (`src/issue_flow/cli.py`).** Both `init` and `update`
  gained `--skip-dep-check`. Verified via `uv run issue-flow init --help`.
- **Docs.**
  - `README.md`: new **Prerequisites** section above **Installation**
    with `git`, `gh`, and `uv` entries, a per-OS install table for `gh`,
    and a note about the new check and `--skip-dep-check` bypass. The
    `issue-flow init` / `update` option tables and the Usage shell
    block were updated to list the flag.
  - `HISTORY.md`: new `[Unreleased]` bullet crediting issue #18.
- **Tests.**
  - New `tests/conftest.py` with an autouse fixture that stubs
    `check_dependencies` to return `[]` by default, so the rest of the
    suite is deterministic regardless of whether the host has `git` /
    `gh` on `PATH`.
  - New `tests/test_dependencies.py` — 11 cases covering the dep list
    scope, presence/absence detection, custom dependency lists, report
    formatting, and the four `prompt_or_skip` branches (empty, skip,
    non-TTY, TTY accept/decline).
  - `tests/test_init.py` gained four cases: proceeds silently when all
    deps present, continues with `skip_dep_check=True`, continues on
    non-TTY stdin, aborts with `typer.Exit(1)` and leaves no scaffold
    when the user declines.

## Verification

- `uv run pytest` → **64 passed** in 6.77s.
- `uv run ruff check src/ tests/` → **All checks passed**.
- Manual smoke:
  - `uv run issue-flow init --help` shows the new `--skip-dep-check` flag.
  - Forcing `gh` to be "missing" via `shutil.which` monkeypatch and
    calling `run_init(..., skip_dep_check=True)` scaffolds the project
    correctly (`Created 20 file(s).`).
  - The same missing-dep path without the skip flag prints the full
    install-hint report and reaches the `typer.confirm` prompt as
    designed.

## Remaining work

None — ready for `/issue-close`.
