# Plan: #214 — always run graphify before planning

## Goal

Add an opt-in config knob so `/iflow-plan` **runs** `issue-flow graphify`
(AST `update`) before prior-art discovery when enabled — useful when
`graphify-out/` is gitignored and would otherwise be missing/stale at plan time.

## Constraints

- **Not already shipped.** `suggest_graphify` (default `true`) only *suggests*
  skimming / rebuilding; docs and design explicitly say **never auto-runs**.
  This issue needs a separate auto-run knob.
- **Bake at `issue-flow update`** — same pattern as other skill-behaviour knobs
  ([skill-behaviour-knobs.md](.issueflows/04-designs-and-guides/skill-behaviour-knobs.md));
  no runtime agent reads of `config.toml`.
- **Default stays safe.** Historical decision in
  [graphify-integration.md](.issueflows/04-designs-and-guides/graphify-integration.md):
  no surprise auto-rebuilds. New knob defaults **off**.
- **AST-only.** Auto path must call default `issue-flow graphify` →
  `graphify update` (no LLM key). Never auto-`extract`.
- **Templates are source of truth** under `src/issue_flow/templates/`; dogfood
  copies refresh via `issue-flow update`.
- **Scope:** plan-step only (not build/close/yolo auto-dispatch of graphify
  beyond following the plan skill). Top-level `suggest_graphify` unchanged.

### Prior art

- `suggest_graphify` — soft nudge in build/close/iflow/rules templates; default
  `true`; **never auto-runs**. New work: **coexist** (keep soft nudges; add
  separate auto knob for plan).
- Knob plumbing: `DEFAULT_*` + `read_*` in
  [`modes.py`](src/issue_flow/modes.py), `resolve_*` + render context in
  [`config.py`](src/issue_flow/config.py), env seed in
  [`init.py`](src/issue_flow/init.py) `_DOTENV_KEYS`, `config add` comments in
  `modes.py` / `cli.py`, docs in `docs/configuration.md` + skill-behaviour design
  doc. **Mirror** that chain for the new key.
- Graph CLI: [`graphify.py`](src/issue_flow/graphify.py) `run_build` /
  `issue-flow graphify` — agents already invoke this; plan skill will call it
  when the baked flag is true.
- Plan templates:
  [`iflow_plan/SKILL.md.j2`](src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2),
  [`commands/iflow-plan.md.j2`](src/issue_flow/templates/commands/iflow-plan.md.j2)
  — today optional “if GRAPH_REPORT exists, skim”; insert auto-run step
  **before** that skim when flag on.

## Approach

1. **New key** `auto_graphify_on_plan` (bool), default **`false`**.
   Env: `ISSUEFLOW_AUTO_GRAPHIFY_ON_PLAN`. Naming follows `auto_*` auto-behaviour
   pattern in skill-behaviour-knobs.
2. **Wire end-to-end** like siblings: `modes.py` defaults/read/write/comments →
   `config.py` resolve + `template_context` → `_DOTENV_KEYS` → `config add`
   help text → `docs/configuration.md` table → update
   `skill-behaviour-knobs.md` (+ short note in `graphify-integration.md`).
3. **Template behaviour** (skill + command, gated `{% if auto_graphify_on_plan %}`):
   - New early step after preflight / before prior-art graph skim:
     run `issue-flow graphify -C <project_root>` (default `update`).
   - If `graphify` missing / nonzero exit: **report and continue** (do not
     block planning); fall back to grep-only prior art.
   - When flag false: no auto-run (current behaviour).
   - Keep existing “skim GRAPH_REPORT if present” (still useful after a
     successful refresh; still no-op if graph absent).
4. **Tests:** extend config/modes/templating defaults contexts; assert plan
   skill/command mention auto-run only when context true; assert false omits
   the run instruction. Touch `config add` JSON payload expectation if it
   lists knobs.
5. Dogfood: set `auto_graphify_on_plan = true` in this repo’s
   `.issueflows/config.toml` only if we want it here — **default false in
   scaffold**; leave this-repo choice as open question / optional.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/modes.py` | `DEFAULT_AUTO_GRAPHIFY_ON_PLAN`, read/write, toml comment |
| `src/issue_flow/config.py` | resolve + template context + env fallback |
| `src/issue_flow/init.py` | `_DOTENV_KEYS` entry |
| `src/issue_flow/cli.py` / agent config help | mention new key if listed |
| `src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2` | gated auto-run step |
| `src/issue_flow/templates/commands/iflow-plan.md.j2` | same |
| `docs/configuration.md` | document key |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | table row |
| `.issueflows/04-designs-and-guides/graphify-integration.md` | short “plan auto-run (opt-in)” note |
| `tests/test_config.py`, `test_modes.py`, `test_templating.py`, maybe `test_cli.py` | coverage |

## Test strategy

- `uv run pytest` (focus: config / modes / templating / config-add).
- `uv run ruff check src/ tests/`.
- Manual: render plan skill with flag true/false; confirm only true includes
  the `issue-flow graphify` run step.

## Open questions

1. **Default `false` (opt-in)?** Recommended: **yes** — keeps “never surprise
   auto-run” for existing projects; users who gitignore `graphify-out` flip it on.
2. **Name `auto_graphify_on_plan`?** Recommended: **yes** (`auto_*` family).
   Alt: `graphify_before_plan`.
3. **Missing/failing graphify → continue?** Recommended: **yes** (note + proceed).
   Alt: hard-stop plan until installed.
4. **Enable in this dogfood repo’s `config.toml`?** Recommended: **no in this PR**
   (ship default false; user can flip after merge). Say **yes** if you want it on here.
