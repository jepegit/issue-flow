# Plan for issue #18: better documentation on dependencies

## Goal

Make issue-flow's external CLI dependencies (especially GitHub CLI `gh`)
obvious to users, both in the README and at install time: `issue-flow init`
should detect missing dependencies, print install guidance, and require
confirmation before continuing.

## Constraints

- Stay proportional — small utility change, no new runtime deps.
- Preserve existing `run_init` / `run_update` behavior for the happy path
  (all deps present) so current tests keep passing without edits.
- Use the existing `rich.Console` for output (matches current style) and
  `typer.confirm` (Typer is already a dependency) for the prompt.
- Detection must be safe on Windows, macOS, Linux — use `shutil.which` only
  (no subprocess calls that could hang or prompt for creds).
- No hard failure when a dependency is missing and the user opts in — this
  is a warning, not a gate. Missing deps block only if the user declines
  at the prompt.
- Non-interactive callers (CI, tests) must be able to bypass the prompt
  without hanging. Prefer an explicit opt-out flag plus auto-skip when
  stdin is not a TTY.
- Keep the dependency list narrow and accurate: only tools issue-flow's
  scaffolded workflow actually invokes (`git`, `gh`). Do not add `uv` to
  the runtime check — `uv` is an install-time prerequisite, not something
  the scaffold itself shells out to, so it belongs in README only.

## Approach

1. **Add a dependency check helper** in a small new module
   `src/issue_flow/dependencies.py`:
   - A typed record per dependency: `name`, `command`, `purpose`,
     `install_hints` (dict of platform → short hint), `docs_url`.
   - `check_dependencies() -> list[MissingDependency]` using
     `shutil.which`. Returns a list of missing items (empty list when all
     present).
   - `format_missing_report(missing, console)` — renders a `rich` panel or
     plain block listing what is missing, why it matters, and how to
     install it on Windows / macOS / Linux, plus a docs link.

2. **Wire the check into `run_init`** (`src/issue_flow/init.py`) at the
   top, before `_create_issueflow_dirs`:
   - Call `check_dependencies()`.
   - If anything is missing:
     - Print the report.
     - If the new `--skip-dep-check` flag is set, or stdin is not a TTY
       (i.e. `not sys.stdin.isatty()`), continue without prompting (emit
       a one-line note that the check was skipped / non-interactive).
     - Otherwise call `typer.confirm("Continue anyway?", default=False)`.
       If the user declines, exit cleanly via `raise typer.Exit(code=1)`.
   - If everything is present, optionally print a single dim
     "All dependencies detected" line (keeps noise low).

3. **Extend the CLI** (`src/issue_flow/cli.py`) on `init`:
   - Add `--skip-dep-check / --no-skip-dep-check` option (default
     `False`). Pass through to `run_init`.
   - `run_init` signature becomes
     `run_init(project_root, force=False, skip_dep_check=False)`.
   - `run_update` gets the same treatment so that `issue-flow update`
     surfaces missing deps too (same helper, same flag).

4. **README.md** — add a "Prerequisites" section directly before
   "Installation":
   - Required: `git`, `gh` (GitHub CLI).
   - Recommended: `uv` (already covered by the existing install snippet,
     link to https://docs.astral.sh/uv/).
   - Short install pointers per OS for `gh` (Homebrew, `winget`,
     `apt`, link to https://cli.github.com/). Include
     `gh auth login` reminder.
   - Note that `issue-flow init` now runs a dependency check and how to
     bypass it (`--skip-dep-check`).

5. **HISTORY.md** — add an `[Unreleased]` bullet describing the new
   dependency check and prerequisites docs (follow existing changelog
   style).

## Files to touch

- `src/issue_flow/dependencies.py` — new module with
  `REQUIRED_DEPENDENCIES`, `check_dependencies`, `format_missing_report`.
- `src/issue_flow/init.py` — call the check inside `run_init` and
  `run_update`; thread `skip_dep_check` through.
- `src/issue_flow/cli.py` — add `--skip-dep-check` option to `init`
  (and `update`, for symmetry).
- `README.md` — new "Prerequisites" section covering `git`, `gh`, `uv`
  with install hints, plus mention of the init-time check.
- `HISTORY.md` — `[Unreleased]` entry.
- `tests/test_dependencies.py` — new: unit tests for
  `check_dependencies` using `monkeypatch` on `shutil.which`, and for
  `format_missing_report` output.
- `tests/test_init.py` — additions:
  - check is skipped when all deps present (no prompt, no abort).
  - missing dep + `skip_dep_check=True` continues scaffolding.
  - missing dep + non-TTY continues scaffolding (simulate via monkeypatch
    on `sys.stdin.isatty`).
  - missing dep + user declines → `run_init` raises `typer.Exit` and
    does *not* create `.cursor/` scaffold files.

## Test strategy

- `uv run pytest` — existing suite must keep passing (current tests call
  `run_init(tmp_path)` which will now hit the dep check; ensure the
  default behavior with real `gh`/`git` on dev machines is still green,
  and for CI / machines without `gh`, tests must monkeypatch
  `shutil.which` so they never prompt).
- New targeted tests in `tests/test_dependencies.py` and extra cases in
  `tests/test_init.py` as listed above.
- Manual smoke: run `uv run issue-flow init /tmp/demo` with `gh`
  temporarily off `PATH` to verify the warning + prompt flow, and with
  `--skip-dep-check` to verify the bypass.

## Open questions

- Should the check also cover `uv` itself? Current plan says **no** (uv
  isn't invoked by the scaffolded workflow at runtime — it's only an
  install-time prerequisite documented in the README). Confirm.
- Flag name: `--skip-dep-check` vs `--yes` vs `--no-dep-check`. Plan
  picks `--skip-dep-check` for clarity; open to the user's preference.
- Should declining the prompt exit with code `1` (plan default) or `0`
  (treat as "user chose not to continue")? Plan uses `1` so CI notices.
