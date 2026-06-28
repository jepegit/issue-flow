# Issue #94 plan — missing requirement (tomlkit)

## Goal

Guarantee `pyproject.toml` declares every runtime third-party dependency the
package imports, and add a regression guard so a future "missing requirement"
(like the reported `ModuleNotFoundError: No module named 'tomlkit'`) cannot recur
silently.

## Findings (investigation already done)

- `tomlkit>=0.15.0` is **already declared** in `pyproject.toml` (line 24) and
  present in `uv.lock`. It was added in commit `a4d9a0d` (#86) in the *same*
  commit that introduced its import in `src/issue_flow/modes.py`.
- `tomlkit` is genuinely needed: `modes.write_active_mode()` uses it to
  round-trip `config.toml` while preserving user comments/formatting (stdlib
  `tomllib` is read-only).
- Full import audit of `src/issue_flow/**/*.py` (top-level + function-level):
  the only third-party imports are `jinja2`, `dotenv` (python-dotenv), `rich`,
  `tomlkit`, `typer` — **all declared**. Everything else is stdlib (`tomllib`,
  `shutil`, `subprocess`, `re`, `json`, `os`, `sys`, `importlib`, `pathlib`,
  `dataclasses`, `typing`) or intra-package (`issue_flow.*`).
- Conclusion: the source tree at HEAD has **no missing requirement**. The
  reported error came from a **stale installed tool** (`uv tool` venv created
  before `tomlkit` became a dep / from an older build). Confirmed: invoking the
  global `issue-flow` binary still raises the exact `tomlkit` error even though
  source + lock are correct.

## Constraints

- Respect the `uv` toolchain (`uv run pytest`, `uv add`); never bare `python`/`pip`.
- Python 3.13+ (`sys.stdlib_module_names` available).
- Keep the change small and in-scope: a regression test, not a refactor.

### Prior art

- `.issueflows/00-tools/` — empty (no existing dependency-audit helper).
- `tests/test_dependencies.py` — covers *external CLI* deps (git/gh/graphify),
  **not** Python package deps. New test complements it; mirror its style.
- No existing packaging/metadata test found (grep: none import
  `importlib.metadata` in tests).

## Approach

1. **No source change for tomlkit** — it is already correctly declared; confirm
   only.
2. **Add a regression guard** `tests/test_packaging.py`:
   - Read declared deps from `pyproject.toml` via `tomllib`
     (`[project].dependencies`), parse out distribution names.
   - Walk `src/issue_flow/**/*.py`, parse each with `ast`, collect top-level
     module names from every `import` / `from ... import`.
   - Drop stdlib (`sys.stdlib_module_names`) and the package's own `issue_flow`.
   - Map remaining import names → distribution names via
     `importlib.metadata.packages_distributions()` (handles `dotenv` →
     `python-dotenv`).
   - Assert every required distribution appears in declared deps; fail with a
     clear message naming the undeclared import + module if not.
   - This test would have failed had #86 added the `tomlkit` import without the
     dep, exactly the class of bug #94 reports.
3. **Release** — the installed-tool fix is to republish so users reinstall; the
   version bump + publish are handled at `/iflow-close` (`uv version --bump`).

## Files to touch

- `tests/test_packaging.py` (new) — the import-vs-declared-deps regression test.
- (At `/iflow-close`) `HISTORY.md` + version bump — not part of `/iflow-start`.

## Test strategy

- `uv run pytest tests/test_packaging.py` (and full `uv run pytest`).
- `uv run ruff check src/ tests/`.
- Sanity-check the guard works by mentally confirming it flags an undeclared
  import (optionally a temporary local check, reverted).

## Open questions

- **Scope:** is adding the regression test (option above) the desired
  deliverable, or do you only want a confirmation that `tomlkit` is declared
  (close as already-fixed, just bump+republish)? Recommended: add the test — it
  is the durable fix and matches "make sure pyproject has all needed
  requirements."
- **Installed-tool note:** should I add a short troubleshooting note (reinstall
  `uv tool install --force issue-flow`) to the README, or leave that out of
  scope? Recommended: leave out unless you want it.
