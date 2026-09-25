# Plan — Issue #248: option for not stopping in a cycle

## Goal

Make the cycle failure policy (`onfail:stop` vs `onfail:skip`) configurable
project-wide so users who want “park failed issue and continue the queue”
do not have to pass `onfail:skip` on every `/iflow-cycle` run. Default stays
**stop** (today’s safe behaviour).

## Constraints

- **Do not invent a second policy.** Per-run tokens `onfail:stop` /
  `onfail:skip` already exist (#142). This issue only adds a **config default**
  that those tokens override.
- Never weaken yolo safeguards — `skip` still parks and records; it does not
  bypass scope/merge/test stops.
- Same config pattern as siblings: `config.toml` > user-global > env > default;
  bake into skills via `issue-flow update`.
- Templates first under `src/issue_flow/templates/`.

### Prior art

- Cycle skill/command: `onfail:stop|skip` (default hard-coded `stop`) —
  `iflow_cycle/SKILL.md.j2`, `commands/iflow-cycle.md.j2`, docs how-to.
- HISTORY #142: cycle resumability + failure policy.
- Config knobs: `cycle_max_issues`, `pr_merge_method` (enum),
  `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`.
- Toolbox: none needed (config + template bake only).

## Approach

1. **Config key** — add **`cycle_onfail`** (recommended name) under
   `[issueflow]`:
   - type: enum `"stop"` | `"skip"`
   - default: `"stop"`
   - env: `ISSUEFLOW_CYCLE_ONFAIL`
   - Wire: `modes.py` (DEFAULT + read + write_default_config /
     `_commented_issueflow_table`), `config.py` resolve / seed / effective /
     template_context, `config_ops.py` `CONFIG_KEYS`.
   - Reject unknown values the same way as `pr_merge_method`.

2. **Templates** — bake `{{ cycle_onfail }}` into cycle skill + command:
   - Input line: ``onfail:stop`` / ``onfail:skip`` — **default from config
     (`{{ cycle_onfail }}`)**; explicit token wins for this run.
   - Step 3 confirm + step 7: say the effective default is the baked value,
     not always `stop`.
   - Mention in rules / AGENTS cycle blurb only if there is already an
     onfail sentence (keep terse).

3. **Docs**
   - `docs/configuration.md` table row + short note under cycle / label
     flows if present.
   - `docs/how-to/cycle.md` — config default + token override.
   - `skill-behaviour-knobs.md` — add the key to the naming table.
   - Optional one-line design note under
     `.issueflows/04-designs-and-guides/` (or extend an existing cycle
     design doc) linking #248.

4. **Tests**
   - Resolve / config round-trip / seed defaults include `cycle_onfail`.
   - Rendered cycle skill with `cycle_onfail: "skip"` mentions skip as the
     baked default; with `"stop"` keeps stop-as-default wording.
   - `test_doc_configuration` sync (table must list every `CONFIG_KEYS` entry).
   - Existing `test_init_cycle_skill_has_state_file_resume_and_onfail` still
     passes (both tokens still documented).

5. **Out of scope**
   - Changing what counts as a stop condition.
   - Auto-retry of failed issues.
   - Parallel cycle behaviour.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/modes.py` | `DEFAULT_CYCLE_ONFAIL`, read/write/normalize |
| `src/issue_flow/config.py` | resolve + seed + template context |
| `src/issue_flow/config_ops.py` | enum key |
| `src/issue_flow/templates/skills/iflow_cycle/SKILL.md.j2` | bake default |
| `src/issue_flow/templates/commands/iflow-cycle.md.j2` | bake default |
| `docs/configuration.md`, `docs/how-to/cycle.md` | document |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | row |
| `tests/…` | config + templating + init |

## Test strategy

- `uv run pytest` (full suite after changes).
- `uv run ruff check src/ tests/`.
- Spot-check: `issue-flow config set cycle_onfail skip` then
  `issue-flow update` → cycle skill text shows skip as default.

## Open questions

1. **Key name:** `cycle_onfail` = `"stop"|"skip"` (recommended — matches
   tokens and `pr_merge_method` style) vs issue’s `allow_cycle_continuation`
   bool (`true` → skip)?
2. **Should `/iflow-auto` / drive** that invoke cycle inherit the config
   default automatically (yes — they already honour cycle’s onfail) — any
   need to hard-code `onfail:stop` in auto/drive templates when present?
   **Recommend:** leave auto/drive as-is where they say `onfail:stop` as the
   *floor for leave-clean*; only cycle’s default becomes configurable. If
   auto templates literally force `onfail:stop`, keep that unless you want
   overnight runs to skip — call that out on Accept if you disagree.

Default for Accept: **`cycle_onfail` enum**, auto/drive unchanged.
