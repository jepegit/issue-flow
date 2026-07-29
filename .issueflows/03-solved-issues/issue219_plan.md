# Issue #219 — Plan

## Goal

Add config knobs so lifecycle handoffs stop asking twice:

1. After the user **confirms a pick**, chain into `/iflow-plan` (no “continue with plan?” pause).
2. After the user **Accept**s a plan, chain into `/iflow-build` (no “run build?” pause).

## Constraints

- **Templates are source of truth** — edit `src/issue_flow/templates/`, then
  dogfood with `issue-flow update`.
- **Bake at render time** — same pattern as other skill-behaviour knobs
  ([skill-behaviour-knobs.md](.issueflows/04-designs-and-guides/skill-behaviour-knobs.md));
  agents do not re-read `config.toml` at runtime for these.
- **Confirms stay** — pick still asks which issue; plan still stops for
  Accept / Revise / Abort. Knobs only remove the *next-step* pause after that
  confirm.
- **Independent flags** — `auto_plan` / `auto_build` / `auto_close` do not
  imply each other (can combine for pick→plan→build→close).
- **Mode gates** — chain only when the target skill is in the active mode
  (`iflow_plan` / `iflow_build`), mirroring `auto_close` + `iflow_close`.
- **Back-compat** — new keys written on next `issue-flow update` / init.

### Prior art

- `auto_close` — [`modes.py`](src/issue_flow/modes.py) /
  [`config.py`](src/issue_flow/config.py) / Jinja in `iflow_build` +
  `iflow_fix`. **Mirror** for pick→plan and plan→build.
- `auto_graphify_on_plan` — plan-side gated step. **Coexist**.
- Pick Phase 3 handoff —
  `templates/skills/iflow_pick/SKILL.md.j2` (“Ask whether to continue with
  `/iflow-plan`”). **Primary change** for `auto_plan`.
- Plan Accept handoff —
  `templates/skills/iflow_plan/SKILL.md.j2`. **Primary change** for
  `auto_build`.
- Design doc
  [skill-behaviour-knobs.md](.issueflows/04-designs-and-guides/skill-behaviour-knobs.md)
  (`auto_*` naming). **Extend**.
- Tests: `test_start_auto_close_chains_into_close`,
  `test_iflow_plan_auto_graphify_on_plan_gated`, config/modes round-trips.
  **Mirror**.
- Toolbox: nothing. Graph: `resolve_auto_close` (community 5),
  skill-behaviour-knobs (community 71).

## Approach

### 1. Knobs

| Key | Env | Default | Effect |
|---|---|---|---|
| `auto_plan` | `ISSUEFLOW_AUTO_PLAN` | **`true`** | After pick confirm (+ branch/init), follow `/iflow-plan` immediately |
| `auto_build` | `ISSUEFLOW_AUTO_BUILD` | **`true`** | On plan **Accept**, follow `/iflow-build` immediately |

Wire each like `auto_close`:

1. `modes.DEFAULT_AUTO_*`, `read_auto_*`, persist in `write_config` / init table.
2. `Settings.resolve_auto_*` + `template_context()`.
3. CLI/docs knob lists (`cli.py`, agent config blurb, `docs/configuration.md`).

**Resolved:** defaults **`true`** (pick confirm / plan Accept already are the
gates; second ask is noise).

### 2. `/iflow-pick` Phase 3

When pick confirm (and yolo-label routing did **not** take over):

- If `auto_plan` and `"iflow_plan" in included_skills`: after Phase 2
  (branch + init), follow the plan skill immediately. Brief note that
  `auto_plan` chained the handoff.
- Else: ask whether to continue with `/iflow-plan` (today).

**Exception unchanged:** yolo-label → `/iflow-yolo` still skips the plan
handoff.

One-shot skip: trailing **`noplan`** on the pick turn (or on confirm)
skips the chain once.

### 3. `/iflow-plan` Accept handoff

- If `auto_build` and `"iflow_build" in included_skills`: on **Accept**,
  follow the build skill immediately. Announce `auto_build` chain.
- Else: tell the user to run `/iflow-build`.

One-shot skip: trailing **`nobuild`** (on Accept turn or `/iflow-plan …`).

Relax the Constraints line “Do not proceed to implementation from this
skill” so the gated Accept→build chain is allowed when `auto_build` is on
(still no code edits *before* Accept).

### 4. Docs / design

- Append both rows to `skill-behaviour-knobs.md` (`auto_*` table + note that
  flags are independent; `noplan` / `nobuild` overrides).
- `docs/configuration.md` + example snippet.
- Workflow doc: pick Phase 3 + plan Accept handoff wording.
- Rules / AGENTS only if they restate handoffs (via `update`).

### 5. This repo dogfood

Explicit `auto_plan = true` / `auto_build = true` in
`.issueflows/config.toml` (optional clarity; matches defaults) +
`issue-flow update`.

### Out of scope

- Implying yolo / auto-merge.
- Auto-picking an issue without user confirm.
- Runtime agent reads of `config.toml` (rejected in #182).

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/modes.py` | defaults, read, write `auto_plan` + `auto_build` |
| `src/issue_flow/config.py` | resolve + template context |
| `src/issue_flow/cli.py` | knob mentions if listed |
| `src/issue_flow/agent.py` | config-knobs blurb if present |
| `src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2` | Phase 3 `auto_plan` + `noplan` |
| `src/issue_flow/templates/commands/iflow-pick.md.j2` | same |
| `src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2` | Accept→build + `nobuild` |
| `src/issue_flow/templates/commands/iflow-plan.md.j2` | same |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | pick + plan handoff wording |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | document both |
| `docs/configuration.md` | table + example |
| `tests/test_modes.py`, `test_config.py`, `test_templating.py` | round-trip + render gates |
| `.issueflows/config.toml` | optional explicit trues |
| dogfood `.cursor/skills/*` via `issue-flow update` | after templates |

## Test strategy

- `uv run pytest` — modes/config resolve (default true, toml false, env);
  templating: off → ask / “run `/iflow-*`”; on → follow next skill; token
  docs present (`noplan` / `nobuild`).
- `uv run ruff check src/ tests/`.

## Open questions

- None — defaults **`true`**, overrides **`noplan`** / **`nobuild`**, and
  pick→plan addition are agreed.
