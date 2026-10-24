# Plan: issue #101, opt-in git hook that routes done issue groups on commit

## Goal

Add an opt-in `pre-commit` hook, installed by `issue-flow init --install-hooks` or `issue-flow hooks install`. On each commit it moves `issue<N>_*` groups whose status file says `- [x] Done` from `01-current-issues/` to `03-solved-issues/`, and stages the move so it lands in the same commit. It is off by default and coexists with existing hooks.

## Constraints

- Opt-in only. Nothing is installed unless a flag or command asks for it. `issue-flow update` refreshes an installed hook script and never installs one.
- **Done-only routing.** The hook moves only `- [x] Done` groups to `03-solved-issues/`. Moving an unfinished group to `02-partly-solved-issues/` stays with `/iflow-pause` and `/iflow-close`, because a commit on an issue branch with `- [ ] Done` is normal mid-work and must leave the focus issue in `01`. This is the same rule `/iflow-cleanup` step 7 already uses.
- The hook stages only the paths it moved, never anything else.
- It never fails a commit because of issue-flow. If `issue-flow` is missing, the hook prints a one-line notice and exits 0. A real error is reported and also exits 0. `git commit --no-verify` and `ISSUEFLOW_SKIP_HOOKS=1` skip it.
- **Coexistence:**
  - Resolve the hooks directory with `git rev-parse --git-path hooks`, which respects `core.hooksPath` (Husky) and linked worktrees, where `.git` is a file.
  - Never overwrite a foreign `pre-commit` hook: refuse and print the line to add to it.
  - For the pre-commit framework, document a `repo: local` entry that calls the same command.
- **Windows:** symlinks need elevated rights there, so fall back to copying the script (with an issue-flow marker line) when `symlink_to` fails. The rest of the hook is POSIX `sh`, which Git for Windows provides.
- **Earlier decision to revisit:** `scaffolding-and-editors.md` (line 625) rejected "a git-hook/daemon to move issue files" in favor of an explicit `agent sweep`. An opt-in, previewable hook doesn't contradict that, but the design note gets an update.

### Prior art

- `tracking.plan_sweep` / `apply_sweep` / `file_marks_done` / `_DONE_RE` in `src/issue_flow/tracking.py`: reuse them. A `done_only` filter goes on the plan, rather than a parallel parser.
- `agent sweep` (`cli.py:1311`, `agent.run_sweep`): the hook command mirrors its `--dry-run` / `--json` shape.
- `scaffolding-and-editors.md` "Deferred" (line 95): the #23 phase-2 editor hooks (`post-checkout` / `pre-push`) are to be composed separately from #101. Keep the hooks module generic (one hook name to one script) so #23 can add its hooks later, but ship only `pre-commit` here.
- `.issueflows/00-tools/`: nothing relevant. `verify_scaffold.py` doesn't cover hooks and stays untouched.

## Approach

1. **`tracking.py`:** add `done_only: bool = False` to `plan_sweep`. When set, skip groups that are not done, and don't exempt the focus issue (a done focus group is finished, which is exactly what close step 4 does).
2. **New `src/issue_flow/hooks.py`** (pure functions plus thin git calls):
   - `hooks_dir(root)`: `git rev-parse --git-path hooks`, resolved against the repo root.
   - `install(root, *, force=False)`: write `.issueflows/hooks/pre-commit` from a template, then symlink it into the hooks dir, or copy it on Windows. Return a result object: `installed` / `already` / `foreign` (refused, with a chain snippet) / `copied`.
   - `uninstall(root)`: remove the link or copy only when it carries the issue-flow marker.
   - `status(root)`: say whether the hook is installed, how (link or copy), and the hooks path in use.
   - `run_pre_commit(root)`: run `plan_sweep(done_only=True)`, then `apply_sweep`, then `git add -A -- <old paths> <new paths>`, and print one line per moved group.
3. **Template `src/issue_flow/templates/hooks/pre-commit.sh.j2`:** a POSIX `sh` script with a marker comment and the `ISSUEFLOW_SKIP_HOOKS` guard. It runs `issue-flow hooks run pre-commit -C "$(git rev-parse --show-toplevel)"`, or prints a notice and exits 0 when `issue-flow` isn't found.
4. **CLI:** a new `hooks` Typer group (`hooks install|uninstall|status|run <name>`), and `init --install-hooks`, which calls `hooks.install` after scaffolding.
5. **`update`:** if `.issueflows/hooks/pre-commit` exists, re-render it. A symlinked install then picks it up automatically; a copied install gets re-copied.
6. **Docs:**
   - README: a "Git hooks (opt-in)" section covering enable/disable, done-only behavior, Husky and pre-commit snippets, and `--no-verify` / `ISSUEFLOW_SKIP_HOOKS`. Drop the item from "Future plans".
   - Design note: a decision record in `scaffolding-and-editors.md` (context, decision, alternatives: post-commit, two-way routing).

## Files to touch

- `src/issue_flow/tracking.py`: the `done_only` option on `plan_sweep`.
- `src/issue_flow/hooks.py`: new.
- `src/issue_flow/templates/hooks/pre-commit.sh.j2`: new.
- `src/issue_flow/cli.py`: the `hooks` group and `init --install-hooks`.
- `src/issue_flow/init.py`: the `install_hooks` parameter, and re-rendering the hook script on `update` when present.
- `tests/test_hooks.py`: new.
- `tests/test_tracking.py`: a `done_only` case.
- `README.md`, `.issueflows/04-designs-and-guides/scaffolding-and-editors.md`, and `test-registry.md` (new rows).

## Test strategy

- `tests/test_hooks.py`, against real temporary git repos (`git init`):
  - Install creates the script and the link.
  - Install is idempotent.
  - A foreign hook is refused.
  - `core.hooksPath` is respected.
  - Install works from a linked worktree (`git worktree add`).
  - Uninstall leaves a foreign hook alone.
  - `run pre-commit` moves a done group, stages the move, and leaves an undone group in `01`.
  - **End to end:** `git commit` with the hook installed, and the commit contains the rename.
  - `ISSUEFLOW_SKIP_HOOKS=1` is a no-op.
- `tests/test_tracking.py`: `plan_sweep(done_only=True)` ignores undone groups and includes a done focus group.
- Run `uv run pytest`, `uv run ruff check src/ tests/` and `uv run issue-flow doctor`.
- Smoke test in a throwaway repo: `issue-flow init . --skip-dep-check --install-hooks`, tick Done, commit, and check the files moved.

## Open questions

1. **Pre-commit or post-commit?** I recommend **pre-commit**: the move lands in the same commit. A post-commit hook would leave a dirty tree after every commit, and `agent switchback` refuses to run on a dirty tree.
2. **Done-only, or two-way routing?** I recommend **done-only**. Two-way routing would push the focus issue to `02` on every mid-work commit.
3. **Existing foreign `pre-commit` hook:** refuse and print a chain snippet (recommended), or add a `--chain` option that wraps the old hook? I'd leave `--chain` out of v1.
4. **Record the setting in `config.toml`** (`git_hook = true`) so `doctor` can flag a missing link? I recommend not doing it in v1: the presence of `.issueflows/hooks/pre-commit` is the record. A config knob can be a follow-up.
