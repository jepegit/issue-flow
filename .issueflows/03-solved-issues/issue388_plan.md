# Plan — Issue #388: more knobs for automatically accepting and for continuing

## Goal

Opt-in knobs so `/iflow-cleanup` can skip the Phase A1 yes and the Phase A2
yes, plus the missing “continue to cleanup” knob. `issue-flow update` warns
when the A2 knob is on. Existing continue knobs stay; the design doc lists
every step so the set is visible in one place.

## Constraints

- Same bake path as `cleanup_include_github` / `auto_plan`: project
  `config.toml` > user-global > `ISSUEFLOW_*` > default, rendered by
  `issue-flow update`. Agents do not freestyle-read `config.toml`.
- Defaults **false**. A1’s yes still does not imply A2. Phase B, workspace
  walk, and `unique_work` stay ask / never-delete.
- `auto_cleanup` does not merge. Yolo already merges. This knob only
  **watches** until the PR is merged (budget: `checks_watch_minutes`), then
  runs `/iflow-cleanup`. Still open when the budget ends → stop and report.
- Do not turn the knobs on in this repo’s `config.toml`. Ship the feature;
  enabling is a later `issue-flow config set`.
- Templates first. Re-render this repo with `issue-flow update` so the
  installed skills match.

### Prior art

- Continue chain (independent; each skips only its own pause): `auto_plan`
  (pick → plan), `auto_build` (Accept → build), `auto_close` (build → close).
  `remind_cleanup` is a nudge, never a run. No cleanup continue knob.
  Mirror that independence; do not fold cleanup into `auto_close`.
- Cleanup confirms: `iflow_cleanup` Phase A1 vs A2 (`#243`). `drive` /
  `landed` already skips both asks for the orchestrator. These knobs are the
  human-config version of that skip, still printing the action list and tip
  SHAs.
- Warning site: `issue-flow update` → `run_update` in `src/issue_flow/init.py`.
  `agent self-update` calls `update`, so it inherits the warning. One warning
  there, not a second copy inside self-update.
- Design inventory: `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`,
  `docs/configuration.md` settings table.
- Toolbox: none. Graph: not required (knob plumbing is the `on_bleeding_edge`
  path in `modes.py` / `config.py` / `config_ops.py`).

## Approach

1. **Accept knobs** (bool, default false)
   - `cleanup_yes_a1` — print the Phase A1 list, then run it. No yes/no.
   - `cleanup_yes_a2` — print squash / divergent names and tip SHAs, then
     `-d` and fall back to `-D`. No yes/no. Still never touches
     `unique_work` or `skipped`.
   - One-shot opt-out tokens: `ask a1`, `ask a2` (force that prompt even
     when the knob is on).
   - Bake the branch into `iflow_cleanup` skill + command templates and the
     workflow doc. A1 text must say it does not authorize A2.

2. **Update warning**
   - At the end of a successful `issue-flow update` (single repo and each
     repo in `--all`), if the effective `cleanup_yes_a2` is true, print one
     short line: cleanup will `git branch -D` squash-landed branches without
     asking. No warning for A1. JSON `--all` includes a `cleanup_yes_a2`
     boolean instead of mixing a sentence into the payload.

3. **Continue knob**
   - `auto_cleanup` (bool, default false). Independent of `auto_close`.
   - Close / yolo / cycle templates: when true, after the PR exists, watch
     until `state=MERGED` (reuse the close yolo watch budget), then follow
     `/iflow-cleanup`. Do not merge from this knob. If the PR is already
     merged (yolo just did), run cleanup immediately.
   - Cleanup then honours `cleanup_yes_a1` / `cleanup_yes_a2`. Phase B stays
     off unless its own knob or token says otherwise.
   - `remind_cleanup` still applies when `auto_cleanup` is false.

4. **Inventory**
   - In `skill-behaviour-knobs.md`, add a “Continue to next step” table:
     pick confirm (always ask) → capture (part of pick, no knob) →
     `auto_plan` → `auto_build` → `auto_close` → `auto_cleanup`.
     Note that cleanup cannot run until the PR is merged, which is why
     `auto_cleanup` watches and does not merge.
   - Add the three keys to the settings table and `docs/configuration.md`.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/modes.py` | defaults, read/write, commented table |
| `src/issue_flow/config.py` | resolve + template context |
| `src/issue_flow/config_ops.py` | bool key specs |
| `src/issue_flow/init.py` | A2 warning after update |
| `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2` | A1/A2 skip + tokens |
| `src/issue_flow/templates/commands/iflow-cleanup.md.j2` | same |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | `auto_cleanup` handoff |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | command reference |
| `docs/configuration.md` | settings rows |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | inventory + decision |
| `tests/test_modes.py`, `test_config.py`, `test_templating.py`, `test_cli.py` or `test_init.py` | resolve, baked text, warning |

## Test strategy

- `uv run pytest` for the new resolve / template / warning tests.
- `uv run ruff check src/ tests/`.
- No essential mark unless a test guards a safety rule (A2 still refuses
  `unique_work`). Recommend leaving new tests unmarked; confirm at close.

## Open questions

1. **Merge vs watch.** Recommend: `auto_cleanup` only watches. Merging stays
   yolo or a human. Accept means this. Say **merge** if you also want a
   non-yolo auto-merge knob.
