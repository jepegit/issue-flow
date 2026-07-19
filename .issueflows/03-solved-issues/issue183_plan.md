# Issue #183 — plan: rename `iflow-start` → `iflow-build`

## Goal

Rename the post-plan implement step from **`/iflow-start`** to **`/iflow-build`** (skill + command + all references), prune the old scaffold surfaces on `issue-flow update`, and update docs — freeing `start` for a future prep skill (out of scope here).

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; edit those, not already-rendered copies in this repo’s `.cursor/` (dogfood refresh via `issue-flow update` / close as usual).
- Comment mandate: **update the docs**.
- Behaviour of the step stays the same — rename only (plus retirement prune).
- Do **not** invent the new auto-loaded “start” prep skill in this issue (issue text only motivates freeing the name).
- Skill-authoring rules still apply (YAML `name:`, invocation forms, etc.).

### Prior art

| Hit | Role | Plan |
| --- | --- | --- |
| `templating.py` `COMMAND_NAMES` / `SKILL_DIRS` / `RETIRED_*` | Surface registry + prune-on-update | Rename stems; add `iflow-start` / `iflow-start` skill folder to retired lists |
| `init.py` / `surfaces.py` `_prune_retired_files` | Deletes retired command/skill paths on update | Reuse — no new prune logic |
| `tracking.py` `STAGE_START` + `STAGE_NEXT_COMMAND` | `agent state` stage / `next_command` | Rename stage + command mapping (see Open questions) |
| `step_profiles.toml` `iflow_start` | Model directive profile | Rename key → `iflow_build` |
| `modes.toml` simple mode lists | Includes start skill/command | Swap to build |
| Pre-v0.5 `issue-start` → `iflow-start` rename | Pattern for retirement | Mirror for `iflow-start` → `iflow-build` |
| Toolbox `verify_scaffold.py` | No hard-coded `iflow-start` today | Touch only if assertions break |
| Graph community ~ skill templates / `iflow-start` node | Confirms template-centric surface | Grep-driven rename |

## Approach

### Rename mechanics (hard cut — recommended)

1. **Templates**
   - Move `skills/iflow_start/` → `skills/iflow_build/` (git mv).
   - Move `commands/iflow-start.md.j2` → `commands/iflow-build.md.j2`.
   - Inside both: `name: iflow-build`, titles/headings `/iflow-build`, `iflow_step = "build"`, prose “start” → “build” where it means this step (keep English verbs like “start work” only when not the command name).
2. **Registries**
   - `COMMAND_NAMES`: `iflow-start` → `iflow-build`.
   - `SKILL_DIRS`: `iflow_start` → `iflow_build`.
   - `RETIRED_COMMANDS` += `iflow-start`; `RETIRED_SKILLS` += `iflow-start` (folder name as emitted).
   - `step_profiles.toml`: `iflow_build = "reasoning"`.
   - `modes.toml` simple lists: swap stems.
3. **Agent state / dispatcher**
   - `tracking.py`: `STAGE_START` → `STAGE_BUILD = "build"`; map to `/iflow-build`.
   - All lifecycle skills/commands that say “never from `/iflow-start`” or chain `… → start → …` → `build`.
   - `/iflow` state C dispatches to `/iflow-build`; yolo chain `init → plan → build → close`.
4. **Docs & product copy**
   - `docs/issue-workflow.md.j2`, `rules/_body.md.j2`, `README.md`, packaged `docs/*.md` if checked in, site `docs/index.md` / `configuration.md` as needed, `modes.py` help strings mentioning `/iflow-start`.
   - Design note: `.issueflows/04-designs-and-guides/rename-start-to-build.md`.
5. **Tests**
   - Global replace of stems in `tests/`; update `agent state` expectations (`stage == "build"`, `next_command == "/iflow-build"`).
   - Init/scaffold tests that assert `iflow-start/` path → `iflow-build/`.
   - Optional: assert `issue-flow update` prunes old `iflow-start` skill/command when present.
6. **Compat**
   - **No** lasting alias for `iflow start` / `/iflow-start` (frees the name). Old scaffolds cleaned by `RETIRED_*` on update.
7. **HISTORY** — Unreleased bullet on `/iflow-close` (not during plan/start).

### Ordering

Rename template files first → registries → tracking → mass reference update → tests → design note → `uv run pytest` + ruff.

### Out of scope

- New auto-invoked “start”/bootstrap skill.
- Renaming English words unrelated to the command (e.g. “before starting implementation”).
- Version bump unless requested at close.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/iflow_start/` → `iflow_build/` | Rename dir + rewrite skill |
| `src/issue_flow/templates/commands/iflow-start.md.j2` → `iflow-build.md.j2` | Rename + rewrite |
| Other `templates/**/*.j2` referencing start step | Point at `/iflow-build` |
| `src/issue_flow/templating.py` | Registries + retired lists |
| `src/issue_flow/step_profiles.toml` | Key rename |
| `src/issue_flow/modes.toml` | Simple mode stems |
| `src/issue_flow/tracking.py` | Stage + next_command |
| `src/issue_flow/modes.py` (help strings) | Wording |
| `README.md`, `docs/*.md`, design note | Docs |
| `tests/test_*.py` | Expectations |
| `.issueflows/04-designs-and-guides/rename-start-to-build.md` | Decision record |

## Test strategy

- `uv run pytest`
- `uv run ruff check src/ tests/`
- Spot-check: render `iflow-build` skill/command; `agent state` after plan-without-done → `/iflow-build`; prune test or manual throwaway `update` if easy.

## Open questions

1. **Compat alias?** Recommended: **hard cut** (no `iflow start` → build). Prefer temporary alias for one release?
2. **`agent state` stage string?** Recommended: rename `"start"` → `"build"` (matches command). Keep `"start"` internally and only change `next_command`?
