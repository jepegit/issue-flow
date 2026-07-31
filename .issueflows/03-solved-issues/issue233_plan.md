# Plan — Issue #233: cleanup configurable

## Goal

Make post-merge cleanup stay out of the lifecycle unless the user asks for it,
and add a config knob for the optional GitHub remote-branch audit (Phase B).

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; bake knobs at
  `issue-flow update` (same pattern as #182 / [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md)).
- `/iflow-cleanup` stays **off-path** — never auto-dispatched by `/iflow`,
  `/iflow-yolo`, `/iflow-cycle`, or `/iflow-close`.
- Do not weaken Phase A/B confirms; never `-D` / `--force`.
- Scope: knobs + wording/gating + docs/tests. No rewrite of the audit CLI.

### Prior art

- Soft nudge knob: `remind_cleanup` (`DEFAULT_REMIND_CLEANUP = True`) in
  [`modes.py`](../../src/issue_flow/modes.py) / [`config.py`](../../src/issue_flow/config.py);
  already gates close / yolo / cycle / iflow-D / fix reminders and most of
  rules branch-hygiene. Intent documented in
  [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md):
  **soft reminder**, not auto-run.
- Gap: rules when `remind_cleanup=true` say **“run `/iflow-cleanup`”**
  ([`_body.md.j2`](../../src/issue_flow/templates/rules/_body.md.j2)), and
  [`issue-workflow.md.j2`](../../src/issue_flow/templates/docs/issue-workflow.md.j2)
  / [`iflow_auto`](../../src/issue_flow/templates/skills/iflow_auto/SKILL.md.j2)
  still nudge cleanup without `{% if remind_cleanup %}`. That matches the bug
  report (“cleanup always happening”).
- GitHub Phase B: trailing tokens only today
  ([github-branch-audit.md](../04-designs-and-guides/github-branch-audit.md));
  no config default yet.
- Toolbox: none needed (`verify_scaffold.py` only if a cheap marker helps).

## Approach

### 1. Keep `remind_cleanup` as the “in-flow or not” switch (no duplicate knob)

| Value | Behaviour |
|-------|-----------|
| `true` (default) | Soft **reminders** after close / cycle / dispatcher-D / fix — never auto-run cleanup |
| `false` | No in-flow cleanup nudges; cleanup only when user runs `/iflow-cleanup` |

**Fix the mandate wording** wherever `remind_cleanup=true` currently tells agents
to **run** cleanup (rules + close command “Once the PR is merged, run…”): change
to remind/suggest language aligned with the design doc.

**Close gating gaps** — wrap leftover in-flow reminders in `{% if remind_cleanup %}`:

- `templates/docs/issue-workflow.md.j2` (close “after review”, fix finish,
  cycle result, dispatcher “when relevant” example)
- `templates/skills/iflow_auto/SKILL.md.j2` (“Remind `/iflow-cleanup` after merges”)

Reference docs that merely *describe* the cleanup command (command table,
dedicated cleanup section) stay ungated.

### 2. New knob: `cleanup_include_github` (comment ask)

| Key | Default | Effect |
|-----|---------|--------|
| `cleanup_include_github` | `false` | When `true`, `/iflow-cleanup` runs Phase B by default (same as trailing `include GitHub`). When `false`, Phase B only via existing tokens. |

- Wire like siblings: `DEFAULT_*` / `read_*` / `resolve_*` / seed /
  `write_default_config` / `_commented_issueflow_table` / `template_context` /
  env `ISSUEFLOW_CLEANUP_INCLUDE_GITHUB`.
- Bake into cleanup skill + command: if config true **or** trailing GitHub
  token → Phase B. Optional override token `no github` / `local only` to skip
  Phase B when the config default is on.
- Update [github-branch-audit.md](../04-designs-and-guides/github-branch-audit.md)
  + [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md)
  + `docs/configuration.md`.

### 3. Docs clarity

In `docs/configuration.md` (and knobs design note): spell out that
`remind_cleanup = false` is the “never in the flow” setting; true only
reminds, never auto-runs.

## Files to touch

- `src/issue_flow/modes.py`, `config.py` — new knob plumbing + comments table
- `src/issue_flow/templates/rules/_body.md.j2` — soften “run cleanup” → remind
- `src/issue_flow/templates/commands/iflow-close.md.j2`,
  `skills/iflow_close/SKILL.md.j2` — same soften where imperative
- `src/issue_flow/templates/docs/issue-workflow.md.j2`,
  `skills/iflow_auto/SKILL.md.j2` — gate leftovers on `remind_cleanup`
- `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2`,
  `commands/iflow-cleanup.md.j2` — honour `cleanup_include_github` + override
- `docs/configuration.md`,
  `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`,
  `github-branch-audit.md`
- `tests/test_config.py`, `test_modes.py`, `test_templating.py` (and cli seed
  asserts if present)

## Test strategy

- `uv run pytest` — extend resolve/seed/read round-trips for
  `cleanup_include_github`; template render asserts for
  `remind_cleanup` true/false wording and cleanup Phase B default on/off.
- `uv run ruff check src/ tests/`

## Open questions

1. **Soften `remind_cleanup=true` from “run” → “remind”?**  
   **Recommended: yes** — matches design doc and the issue (“never happen in
   the flow” unless user issues it). Alternative: keep “run” when true and
   tell users to set `false` only (weaker fix; agents keep auto-cleaning).

2. **GitHub knob name / default?**  
   **Recommended: `cleanup_include_github = false`** with `no github` /
   `local only` override. Alternative names: `include_github_cleanup`,
   `cleanup_github_default`.

3. **Also gate the always-on rules lifecycle bullet that lists `/iflow-cleanup`
   as step 6?**  
   **Recommended: leave the command in the lifecycle list** (discovery); only
   gate/soften the “after PR merges, run it” hygiene mandate.
