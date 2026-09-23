# Plan: #307 noob mode

## Goal

Add a **`noob` knob** (default **off**). When on, every lifecycle step
ends with a short “what’s next” footer: the recommended next command plus
a small list of relevant `/iflow-*` commands. Teach the loop without
auto-dispatching extra steps.

## Constraints

- Distinct from scaffolding **`novice` mode** (`--mode novice`): that
  *installs* a smaller command surface. This knob only *explains* next
  steps, and can be on in `standard`.
- Bake at `issue-flow update`, same as `remind_cleanup` / `suggest_graphify`.
  Agents do not runtime-parse `config.toml`.
- Never auto-run the suggested command. `auto_plan` / `auto_build` stay
  independent.
- Default **off** so existing `standard` projects stay quiet.
- No new helper script in `00-tools/`.

### Prior art

- `remind_cleanup` / `suggest_graphify` — existing soft-nudge knobs baked
  into skill/command templates (`skill-behaviour-knobs.md`).
- `issue-flow agent state` + `tracking.STAGE_NEXT_COMMAND` — deterministic
  next linear command (`/iflow-capture|plan|build|close`).
- `/iflow` dispatcher already routes the linear step; off-path hints are
  already gated on `remind_cleanup` / `suggest_graphify`.
- `[modes.novice]` + `NOVICE_CONFIG` — stop-and-ask preset; does **not**
  currently print a next-command catalog after each step.
- `novice-onboarding.md` — CLI reports / agent acts; keep that split.

## Approach

1. **Knob.** `[issueflow] noob = false`. Env `ISSUEFLOW_NOOB`. Wire
   `Settings.resolve_noob`, `modes.read_noob`, `config_ops`, default
   `config.toml` comment, `issue-flow config show|set`.
2. **Novice seed.** Add `noob = true` to `NOVICE_CONFIG` only (first-time
   `--mode novice`). Existing `config.toml` is never rewritten.
3. **Shared footer include.** New
   `templates/skills/_noob_next.md.j2` (and a thin command twin or the
   same include). When `noob` is true, each lifecycle skill’s Report /
   Hand-off section:
   - Run `issue-flow agent state --json` and print
     `next_command` as **Recommended**.
   - Print a **Relevant next** list for *this* stem (3–6 commands),
     not the full catalog. Linear path first; then nearby off-path
     (`/iflow-status`, `/iflow-pause`, `/iflow-cleanup`, `/iflow-pick`)
     when they make sense for that step.
   - One-line why. Chat + slash forms (`iflow plan` / `/iflow-plan`).
4. **Where it appears.** All *installed* lifecycle stems (honour
   `included_skills`). Hands-off paths (yolo / cycle) still get a short
   footer if those skills are installed — they are not the noob default
   surface.
5. **Docs.** `docs/configuration.md` table + `skill-behaviour-knobs.md`
   row. One sentence in `how-to/choose-a-mode.md` that `noob` ≠ `novice`.
6. **This repo.** Leave `noob` off in issue-flow’s own `config.toml`
   unless we opt in later.

## Files to touch

- `src/issue_flow/config.py`, `modes.py`, `config_ops.py`, `cli.py` —
  resolve / persist / help text.
- `src/issue_flow/templates/skills/_noob_next.md.j2` — shared footer.
- Lifecycle `SKILL.md.j2` / `commands/*.md.j2` — include the footer.
- `src/issue_flow/templates/docs/configuration.md.j2` (or `docs/` if
  not generated) + `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`.
- `tests/test_config.py`, `test_templating.py`, `test_novice_mode.py` —
  default off; on → footer present; novice seed writes `noob = true`.

## Test strategy

`uv run pytest` (and `uv run ruff check src/ tests/`). New tests: default
`resolve_noob` is false; config/env flip; rendered pick/plan/close skills
contain the footer iff `noob` is true; `seed_novice_config` writes
`noob = true` and does not overwrite an existing file.

## Open questions

1. **Name:** `noob` (issue text, distinct from `novice`) vs `noob_mode`
   vs a milder `guide_next`?
2. **Seed `noob = true` on first-time `--mode novice`?** Recommended:
   yes.
3. **Footer on yolo/cycle/epic too**, or only the linear + status/pick
   surface?
