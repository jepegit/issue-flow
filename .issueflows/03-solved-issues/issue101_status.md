# Status: issue #101

- [x] Done

## What's done

- **Plan.** Accepted on 2026-10-24, with the recommended answers: pre-commit hook, done-only routing, refuse foreign hooks (no `--chain`), and no `config.toml` setting in v1.
- **`tracking.plan_sweep(done_only=True)`.** Plans only `- [x] Done` groups. Without an `except_number`, the focus group is included too.
- **`src/issue_flow/hooks.py`.** Provides `hooks_dir`, which uses `git rev-parse --git-path hooks` so `core.hooksPath` and worktrees work, plus:
  - `install`: writes the script, then symlinks it, or copies it when symlinks fail. It refuses a foreign hook unless `--force` is given.
  - `uninstall`: removes only our hook.
  - `status` and `refresh_installed`.
  - `run_pre_commit`: moves groups and stages only the moved paths (`git rm --cached` for the old paths, `git add` for the new ones). `ISSUEFLOW_SKIP_HOOKS` skips it.
- **Template `templates/hooks/pre-commit.sh.j2`.** A POSIX `sh` script with a marker line. It always exits 0, including when `issue-flow` is missing or fails. It bakes in the project's subpath for nested layouts.
- **CLI.**
  - New `issue-flow hooks install|uninstall|status|run [pre-commit]` group.
  - `init --install-hooks`.
  - `update` re-renders an installed script and never installs one.
- **Docs.**
  - README: CLI overview lines and bullet; "Git hook integration" removed from Future plans.
  - `docs/cli.md`: new `issue-flow hooks` section with a pre-commit framework snippet, plus the `--install-hooks` row.
  - `scaffolding-and-editors.md`: decision record "Git hooks (#101)"; the old "out of scope" line now points at it.
  - `test-registry.md`: two rows.
- **Tests.**
  - `tests/test_hooks.py`: 11 tests on real temporary git repos, including a `git commit` through the installed hook.
  - `tests/test_tracking.py`: one `done_only` test.

## Verification

- `uv run pytest`: 980 passed.
- `uv run ruff check src/ tests/`: clean.
- `uv run issue-flow doctor`: exit 0.
- `scripts/check_doc_links.sh --stage-only`: no issues.
- The wheel contains `templates/hooks/pre-commit.sh.j2`.
- Smoke test in a throwaway repo:
  - `init --install-hooks`, tick Done, commit: the done group lands in `03` in the same commit, the unfinished group stays, and the tree is clean.
  - An older `issue-flow` on `PATH` (no `hooks` command) let the commit through.

## Remaining work

- None. Closed via `/iflow-close` on 2026-10-24. New tests stay unmarked (not essential), matching the rest of `test_tracking.py`.
- Note: the global editable `issue-flow` tool points at the home checkout, so the hook only works there after the merge.
