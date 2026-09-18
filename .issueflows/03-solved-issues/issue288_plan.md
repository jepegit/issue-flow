# Plan — #288 defer_changelog (write on default after merge)

## Goal

Optional `[issueflow].defer_changelog` (default **false**) so issue
branches never touch `HISTORY.md` / `CHANGELOG.md`. The bullet lives in
`issue<N>_status.md` + PR body; cleanup / yolo post-pull appends it on
the default branch (promote there too). Knob off = today's #171 / #240 /
#260 repair path.

## Constraints

- Default **off**. Existing projects keep the bullet in the PR commit.
- `confirm_changelog_update` still gates **whether / what text**; it
  must not write HISTORY on the issue branch when defer is on.
- `nohistory` still skips the bullet entirely.
- Do not replace `sync-branch` / `pr-sync`. Do not add towncrier,
  sidecar `unreleased.md`, or `merge=union`.
- One writer on default: newest last, same order as `history.py` mode A.
- Idempotent if the bullet is already in `[Unreleased]` (or the
  promoted section).

### Prior art

- `src/issue_flow/history.py` — keep-both resolver only (no append API yet).
- `src/issue_flow/templates/skills/iflow_history_update/SKILL.md.j2` — mode A
  append / mode B promote; today always on the issue branch from close.
- `iflow_close` step 3 + “never post-merge” wording (#171).
- `iflow_cleanup` Constraint: “do not offer HISTORY here” — must flip
  for **apply deferred**, not a new offer.
- Parallel cycle already leaves bullets in status; coordinator appends
  (`parallel-cycle.md`). Reuse that recording shape.
- Knob pattern: `confirm_changelog_update` / `locked` in `modes.py` +
  `Settings.resolve_*` + `docs/configuration.md` +
  `skill-behaviour-knobs.md`.
- Toolbox: no helper for changelog apply (`00-tools/` is vendor/verify only).

## Approach

1. **Knob.** `defer_changelog` bool, default `false`. Precedence
   project > user-global > `ISSUEFLOW_DEFER_CHANGELOG` > default.
   `config show` / `set`. Bake into close / cleanup / yolo / cycle /
   history-update / rules templates.

2. **`history.py` writers** (pure text, unit-tested):
   - `append_unreleased_bullet(text, bullet) -> str`
   - `promote_unreleased(text, version, date) -> str` (empty Unreleased
     above the new dated heading)
   - `changelog_has_bullet(text, bullet) -> bool` for idempotence

3. **CLI.** `issue-flow agent apply-changelog --issue N` (default
   branch only; refuse on issue branch). Reads the deferred bullet +
   optional planned version from `issue<N>_status.md` (01 then 03).
   Writes `Settings.history_file`. No-op if missing file, `nohistory`,
   or bullet already present. `--json` for tests.

4. **Close (defer on).** Do **not** edit HISTORY. Write
   `### Deferred changelog` on the status file (bullet text; planned
   version if any). Put the same bullet in the PR body. Step 3 still
   runs the *decision* (`nohistory` / `log` / confirm text) — only the
   **file write** moves.

5. **Cleanup A1 / yolo post-pull.** After FF pull on default, if the
   merged issue has a deferred section, run `apply-changelog`. Commit
   on default: `docs: changelog for #<N>` (issueflows+HISTORY only).
   Yolo `stay` still applies on default from **home** after merge.

6. **Docs.** `skill-behaviour-knobs.md`, `changelog-timing.md` (prevent
   vs #171 “always in the PR”), `pr-queue-sync.md` (Part B shipped),
   `changelog-conflicts.md` (repair stays default-off),
   `docs/configuration.md`.

## Files to touch

- `src/issue_flow/history.py` — append / promote / has-bullet
- `src/issue_flow/modes.py`, `config.py`, `config_ops.py` if needed —
  key + resolve + seed
- `src/issue_flow/agent.py` + `cli.py` — `apply-changelog`
- Templates: `iflow_close`, `iflow_history_update`, `iflow_cleanup`,
  `iflow_yolo`, `iflow_cycle`, `rules/_body.md.j2`, maybe
  `docs/issue-workflow.md.j2`
- Design docs + `docs/configuration.md` + `HISTORY.md`
- `tests/test_history.py` + config/CLI tests

## Test strategy

`uv run pytest` / `uv run ruff check src/ tests/`.

- Knob default false; env + project override; `config show`
- `append` / `promote` / idempotent has-bullet (LF)
- `apply-changelog` on default writes once; refuse on `N-slug` branch
- Template render: defer-on close skill says no HISTORY hunk on the
  issue branch; cleanup mentions apply after pull
- Knob off: close skill still writes HISTORY in the PR commit

## Open questions

1. **Dogfood here?** Leave this repo’s `config.toml` at default `false`
   (recommended) vs set `defer_changelog = true` after ship.
2. **Default-branch commit authoring** — always auto-commit the
   apply-changelog hunk in cleanup/yolo (needed for unattended), or
   confirm when `confirm_changelog_update` is true? Recommend:
   **auto-commit when yolo / cleanup already confirmed**; honour
   confirm only for interactive cleanup if that knob is true.
