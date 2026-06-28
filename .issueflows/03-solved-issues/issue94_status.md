# Issue #94 status — missing requirement (tomlkit)

- [x] Done

## Outcome

No package code change required. Investigation showed `tomlkit>=0.15.0` is
**already declared** in `pyproject.toml` and present in `uv.lock` (added in #86,
the same commit that introduced its import in `src/issue_flow/modes.py`).

## What was done

- **Dependency audit** of `src/issue_flow/**/*.py` (top-level + function-level
  imports): the only third-party imports are `jinja2`, `dotenv`
  (python-dotenv), `rich`, `tomlkit`, `typer` — all declared. Everything else is
  stdlib or intra-package. No missing requirement remains in source.
- **Root cause identified:** the reported `ModuleNotFoundError: No module named
  'tomlkit'` came from a **stale editable `uv tool` install** (installed binary
  reported `v0.4.1a3`, predating #86) running live source against a venv
  resolved before `tomlkit` was a dependency. Not a source bug.
- **Documented the gotcha** in
  `.issueflows/04-designs-and-guides/this-project.md` (new "Editable `uv tool`
  install — dependency refresh gotcha" subsection): rerun
  `uv tool install --force --editable .` after any dependency change; this is
  distinct from the `issue-flow update` subcommand.
- Also filled out the rest of `this-project.md` (was a TODO scaffold).

## Fix for affected users

Reinstall the tool so the venv re-resolves deps:

```bash
uv tool install --force --editable .
```

A republished beta likewise carries the already-declared `tomlkit` dep for
fresh installs.

## Not done (deliberately, per user)

- No regression test added (the proposed `tests/test_packaging.py` import-vs-deps
  guard was discussed but the user opted to keep scope minimal).
- No README troubleshooting note.
