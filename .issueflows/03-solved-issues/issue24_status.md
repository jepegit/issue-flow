# Status — Issue #24: utilize the tools folder and status files better

- [x] Done

## What's done

- Added a scaffolded `00-tools/README.md` template
  (`src/issue_flow/templates/tools/README.md.j2`) — a self-describing toolbox
  index, wired into `init.py` via `_ensure_tools_readme` (run on both init and
  update, never overwritten once present).
- `/iflow-plan` (command + skill): prior-art discovery now checks the toolbox
  first; "None found" bullet updated to `toolbox + grep + graph`.
- `/iflow-start` (command + skill): added a **toolbox** convention (check first,
  contribute back with an index entry); split status handling into an **up-front
  seed** step + a **keep-current** step.
- Strengthened the tools blurb in `rules/_body.md.j2` (check-first +
  contribute-back).
- Updated `docs/issue-workflow.md.j2` (intro toolbox note, `/iflow-plan` and
  `/iflow-start` step descriptions).
- Tests added in `tests/test_init.py` and `tests/test_update.py` (README
  create/preserve under init+update; start/plan wording).

### Version-bump enhancement (folded in, 2026-06-28)

- Rewrote `iflow-version-bump` skill to document **all** `uv version --bump`
  levels (`major/minor/patch/stable/alpha/beta/rc/post/dev`) with an example
  table, plus a **pre-release-aware default** (bare `bump` stays on the current
  alpha/beta/rc/dev channel, else `patch`).
- Updated `/iflow-close` command + skill bump-token mapping and `docs/issue-workflow.md.j2`.
- Confirmed no Python code parses bump levels (docs-only change).
- Added tests: `test_init_version_bump_skill_documents_all_levels_and_default`,
  `test_init_close_skill_documents_prerelease_default`.

## Verified

- `uv run pytest` — 250 passed (incl. tools-README, start/plan wording, and
  version-bump tests).
- `uv run ruff check src/ tests/` — all checks passed.

## Closed out

- Refreshed this repo's rendered `.cursor/` copies via `issue-flow update` (18 files).
- Version bump `0.4.1a4 → 0.4.1a5` (bare `bump` → pre-release-aware default = alpha).
- `HISTORY.md`: two bullets appended under `[Unreleased]` (not promoted — alpha
  cycle accumulates under Unreleased; matches how prior alphas were handled).
- Commit + push + PR via `/iflow-close`.
