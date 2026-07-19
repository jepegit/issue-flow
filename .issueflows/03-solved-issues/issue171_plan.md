# Issue #171 — plan: changelog timing (always in the PR)

## Goal

Make the changelog/`HISTORY.md` update **land in the close commit that feeds the PR** — never as a post-merge afterthought — using (and tightening) the existing `confirm_changelog_update` config rather than inventing a parallel knob.

## Constraints

- Templates are source of truth under `src/issue_flow/templates/`.
- `/iflow-close` already runs history update as **step 3**, before commit / push / PR — the gap is agent behaviour when confirm is declined or when agents re-ask after merge.
- `confirm_changelog_update` already exists (default `true`; `false` = write without ask, same as yolo history). Prefer reuse over a new config key.
- `nohistory` / `skip history` remain the explicit opt-out.
- Scope: skill/docs/config-default behaviour — not a new CLI command.

### Prior art

| Hit | Role | Plan |
| --- | --- | --- |
| `skills/iflow_history_update/SKILL.md.j2` | Writes changelog; confirm gated by `confirm_changelog_update`; **decline → skip + continue close** | Tighten decline path |
| `skills/iflow_close/SKILL.md.j2` + `commands/iflow-close.md.j2` | Step 3 → history, then commit includes `HISTORY.md` | Add hard timing constraints |
| `modes.py` `DEFAULT_CONFIRM_CHANGELOG_UPDATE = True` + `skill-behaviour-knobs.md` | Existing config | Reuse; optional default flip (Open Q) |
| Yolo / cycle | Already write history without confirm | Keep; document as same as `confirm_changelog_update = false` |
| Toolbox | No helper for this | None needed |

## Approach

### Root cause

Close already schedules history **before** the PR. Pain comes from:

1. Confirm decline → “skipped changelog, continue close” → PR merges without HISTORY → agent (or human) asks again after merge.
2. Soft agent drift: offering a HISTORY update after the PR is accepted/merged, outside step 3.

### Behaviour changes (recommended)

1. **Hard timing rule** (close + history-update + rules body + workflow doc):
   - Changelog write happens only in `/iflow-close` step 3 (or yolo’s no-prompt equivalent).
   - **Never** propose updating `HISTORY.md` / CHANGELOG after the PR is open or merged (cleanup must not offer it either).
   - The HISTORY bullet **must** be in the same commit that close pushes for the PR (unless `nohistory`).

2. **Confirm-decline is blocking** (when `confirm_changelog_update` is true):
   - If the user declines the proposed bullet, **stop** — do not continue to issue-folder moves / commit / PR.
   - Offer exactly: **write as proposed** / **revise bullet** / **`nohistory` (explicit skip)** / **abort close**.
   - Silent “skip and continue” is removed.

3. **Config** — reuse `confirm_changelog_update`:
   - Document clearly: `false` = always write during close without asking (best match for “always in the PR”).
   - **Default flip** left as Open question (rec: flip to `false` so new scaffolds match the issue intent; existing `config.toml` values still win on update).

4. **Design note** — update `skill-behaviour-knobs.md` (and a short `changelog-timing.md` if useful) with the decline-blocking rule and “never post-merge” constraint.

5. **Tests** — render asserts: close/history skills mention blocking decline + forbid post-merge updates; if default flips, update `DEFAULT_CONFIRM_CHANGELOG_UPDATE` + tests/docs tables.

### Out of scope

- Auto-creating missing `HISTORY.md`.
- Changing yolo/cycle merge behaviour.
- A second config key parallel to `confirm_changelog_update`.

## Files to touch

| Path | Change |
| --- | --- |
| `templates/skills/iflow_history_update/SKILL.md.j2` | Blocking decline; never post-merge |
| `templates/skills/iflow_close/SKILL.md.j2` + `commands/iflow-close.md.j2` | Same; step-3 / constraints |
| `templates/skills/iflow_cleanup/SKILL.md.j2` (+ command if needed) | Do not offer changelog updates |
| `templates/rules/_body.md.j2` + `docs/issue-workflow.md.j2` | Document timing |
| `modes.py` / `config` defaults | Only if default flips |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` (+ optional `changelog-timing.md`) | Decision record |
| `tests/test_templating.py` (+ config/modes tests if default changes) | Coverage |

## Test strategy

- `uv run pytest`
- `uv run ruff check src/ tests/`
- Focused render tests for the new constraints / default.

## Open questions

1. **Default for `confirm_changelog_update`:** flip to **`false`** (rec — always write in close without ask), or keep **`true`** and only fix decline-blocking + post-merge forbid?
2. **Decline behaviour:** accept **stop + choose write / revise / `nohistory` / abort** (rec), or keep skip-and-continue?
