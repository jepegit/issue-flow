# Status for issue #15: update HISTORY.md when making changes worthy of mentioning

- [x] Done

Plan: [issue15_plan.md](./issue15_plan.md) · Original: [issue15_original.md](./issue15_original.md) · GitHub: <https://github.com/jepegit/issue-flow/issues/15>

## Done so far

- **Design decision:** extend `/issue-close` with a new "update `HISTORY.md`" step (plan recommendation O1). No new slash command added.
- **New skill** `issueflow-history-update` describing both operation modes:
  - append a bullet to `## [Unreleased]` when no version bump happened
  - promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` (with a fresh empty `## [Unreleased]` above) when a bump happened
  - graceful skip when `HISTORY.md` is missing (never auto-created)
  - single confirm-before-write using a diff preview; `nohistory` opts out entirely
- **New config knob** `ISSUEFLOW_HISTORY_FILE` (default `HISTORY.md`) wired through `Settings.history_file`, `Settings.template_context`, and the `.env` scaffold in `run_init`.
- **Templates updated** (all source-of-truth):
  - [`commands/issue-close.md.j2`](../../src/issue_flow/templates/commands/issue-close.md.j2) — new step 3, renumbered remaining steps, and new `nohistory` / `log "..."` / `note "..."` input tokens. Commit step now stages `HISTORY.md` too.
  - [`commands/issue-yolo.md.j2`](../../src/issue_flow/templates/commands/issue-yolo.md.j2) — forwards the new tokens.
  - [`skills/issueflow_issue_close/SKILL.md.j2`](../../src/issue_flow/templates/skills/issueflow_issue_close/SKILL.md.j2) — mirrors step 3 and the new input tokens.
  - [`skills/issueflow_history_update/SKILL.md.j2`](../../src/issue_flow/templates/skills/issueflow_history_update/SKILL.md.j2) — new skill.
  - [`docs/cursor-issue-workflow.md.j2`](../../src/issue_flow/templates/docs/cursor-issue-workflow.md.j2) — `/issue-close` role row, skills table (new skill row), and `/issue-close` section.
- **Python updated:**
  - [`src/issue_flow/config.py`](../../src/issue_flow/config.py) — added `history_file: str` via `ISSUEFLOW_HISTORY_FILE`; exposed in `template_context`.
  - [`src/issue_flow/init.py`](../../src/issue_flow/init.py) — added `("ISSUEFLOW_HISTORY_FILE", "HISTORY.md")` to `_DOTENV_KEYS`.
  - [`src/issue_flow/templating.py`](../../src/issue_flow/templating.py) — registered the new skill template in `TEMPLATE_MANIFEST` (now 20 entries).
- **Regenerated** `.cursor/commands/*`, `.cursor/skills/**`, and `docs/cursor-issue-workflow.md` via `uv run python scripts/update_issueflow_setup.py`.
- **README.md** — added the new skill row, new config-variable row for `ISSUEFLOW_HISTORY_FILE`, and a richer `/issue-close` bullet mentioning the changelog update.
- **Tests added / updated** (49 total now pass, up from 45):
  - `test_config.py` — assert `history_file == "HISTORY.md"` default, `history_file` in the template-context keys, and env override via `ISSUEFLOW_HISTORY_FILE=CHANGELOG.md`.
  - `test_templating.py` — added `history_file` to shared contexts, bumped manifest count from 19 → 20, and added tests for: the `/issue-close` history step (tokens + skill reference), the history-update skill's two modes + missing-file fallback + never-create invariant, `{{ history_file }}` substitution with a custom filename, and `/issue-yolo` token forwarding.
  - `test_init.py` — assert `# ISSUEFLOW_HISTORY_FILE=HISTORY.md` lands in both the fresh `.env` and the append path, include it in the custom-`.env`/force scenario, add `issueflow-history-update` to the skills scaffold check, and add a new test covering `issue-close.md` documenting the HISTORY step.
- **Lint clean:** `uv run ruff check src/ tests/` — all checks passed.

## Remaining work

- **`HISTORY.md` bullet for #15 itself** is deliberately deferred to `/issue-close`, which will dog-food the new step (per the plan's Files-to-touch note). Running `/issue-close` should append something like `- /issue-close now updates HISTORY.md when landing an issue, with promote-on-bump support (#15).` to the `[Unreleased]` section.

No open blockers. Ready for `/issue-close`.

## Notes on plan deltas

- None. All defaults (O1–O6) from the plan were accepted and implemented as described.
- Scope ended up matching the plan exactly: one new skill, one new config knob, one new step in `/issue-close`, matching doc / test / readme updates.
