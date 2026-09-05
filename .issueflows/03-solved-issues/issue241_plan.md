# Plan — Issue #241: rename issue-capture `/iflow-init`, reclaim `/iflow-init` for harness cold-start

## Goal

Stop overloading `/iflow-init`. Today it means "capture this GitHub issue into
`.issueflows/`" (often from the branch name). Rename that lifecycle step to a
clearer verb, and make `/iflow-init` mean "cold-start / (re)scaffold the
issue-flow harness" — aligned with the CLI's `issue-flow init`.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; re-render with
  `issue-flow update`. Behaviour of issue capture must stay intact — only the
  *name* and the new cold-start skill are in scope.
- Every project that already has scaffolded skills inherits the rename on next
  `issue-flow update`. Use the same retire-on-update pattern as #183
  (`iflow-start` → `iflow-build`): old skill/command folders land in
  `RETIRED_*` and get pruned.
- Invocation table in `rules/_body.md.j2` is generated from
  `included_commands` — renaming the command stem updates chat forms
  (`iflow capture`, etc.) automatically. Manual prose that hard-codes
  `/iflow-init` as "capture" must be hunted and fixed.
- `agent.py` uses `_SCAFFOLD_MARKER_SKILL = …/iflow-init/SKILL.md` as the
  "editor is scaffolded" probe (`doctor` / resolve). After the swap that
  marker must still point at a skill that **every** scaffold writes — the new
  cold-start `iflow-init` is fine; do not leave it pointing at a retired name.
- Python 3.13 / `uv`; `uv run pytest`, `uv run ruff check src/ tests/`.

### Prior art

- **#183 rename `iflow-start` → `iflow-build`** — the migration template:
  rename skill dir + command stem, add old names to `RETIRED_COMMANDS` /
  `RETIRED_SKILLS`, update dispatcher/docs/rules, prune on `update`.
  **Follow.**
- **`issue-flow agent capture`** (`agent.py`) — the mechanical half of today's
  `/iflow-init`. Strong argument for naming the skill **`iflow-capture`**:
  skill verb matches the CLI helper agents already call.
- **`issue-flow init` / `run_init()`** (`init.py`) — the real harness
  cold-start. New `/iflow-init` skill should *wrap / guide* this CLI, not
  re-implement scaffolding.
- **`issue-flow update` / `doctor` missing_editor_scaffold** — related
  "harness needs attention" paths; cold-start skill should mention `update`
  and point at doctor when an editor dir exists without skills.
- **`.issueflows/04-designs-and-guides/skill-authoring.md`** — house rules for
  skill templates. **Follow.**
- **Graph:** `run_init()`, `test_init_issue_init_documents_branch_inference`
  — confirms branch-inference docs are pinned in tests; those strings must
  move with the rename.
- **Toolbox:** `verify_scaffold.py` — use after rename to assert both the new
  capture skill and the reclaimed `iflow-init` render.

## Approach

### 1. Capture-skill name — **locked: `iflow-capture`**

Accepted on plan confirm. Matches `issue-flow agent capture`; chat form
`iflow capture 42`.

### 2. Rename today's issue-capture skill/command → `iflow-capture`

Mechanical rename (mirror #183):

| From | To |
|---|---|
| `templates/skills/iflow_init/` | `templates/skills/iflow_capture/` |
| `templates/commands/iflow-init.md.j2` | `templates/commands/iflow-capture.md.j2` |
| skill frontmatter `name: iflow-init` | `name: iflow-capture` |
| `COMMAND_NAMES` / `SKILL_DIRS` entry | `iflow-capture` / `iflow_capture` |
| `RETIRED_COMMANDS` / `RETIRED_SKILLS` | do **not** retire `iflow-init` — that name is reused by step 3 |
| `step_profiles` / any `init` profile key | rename key to `capture` (keep default economy/reasoning as today) |

Sweep **all** hard-coded `/iflow-init` / `iflow-init` / `iflow init` references
that mean *issue capture* — dispatcher, pick, yolo, issue, fix, pause, close
reminders, workflow doc, AGENTS managed block, tests (`test_init_*`,
template consistency). Lifecycle stage: rename suggested command to
`/iflow-capture`; rename stage id `init` → `capture` if nothing external
pins the string (check `tracking.py` / `agent state` JSON).

No compat shim — same as #183. Loud HISTORY + workflow pitfall:
"`/iflow-init` now scaffolds; use `/iflow-capture` to pull an issue".

### 3. New `/iflow-init` = harness cold-start (off-path) — **locked**

New skill + command templates. **Off-path:** `/iflow` must **not**
auto-dispatch to it. Explicit invoke only.

Behaviour sketch:

1. Detect whether `.issueflows/` + agent skills already exist
   (`agent resolve` / marker skill).
2. If **missing:** tell the user to run `issue-flow init [.]` (or
   `uvx issue-flow init`), show the exact command, offer to run it when the
   CLI is on PATH (confirm first). Do not invent a second scaffolder.
3. If **present:** explain that harness is already initialised; point at
   `issue-flow update` for template refresh, `issue-flow update --editor <id>`
   / doctor `missing_editor_scaffold` for adding an editor, and
   `/iflow-capture` for capturing an issue.
4. Never capture a GitHub issue from this skill.

Wire into docs table + rules invocation list via `COMMAND_NAMES`. Keep
`_SCAFFOLD_MARKER_SKILL` as `skills/iflow-init/SKILL.md` (cold-start skill —
always emitted).

### 4. Design doc

Add `.issueflows/04-designs-and-guides/iflow-init-vs-capture.md` recording:
why capture moved, chosen name, cold-start meaning, retire-on-update, and
the #183 precedent.

## Files to touch

| Path | Change |
|---|---|
| `src/issue_flow/templates/skills/iflow_init/` → `iflow_<capture>/` | rename + retitle; body stays capture logic |
| `src/issue_flow/templates/commands/iflow-init.md.j2` → `iflow-<capture>.md.j2` | parity |
| `src/issue_flow/templates/skills/iflow_init/` (new) + `commands/iflow-init.md.j2` (new) | cold-start skill |
| `src/issue_flow/templating.py` | `COMMAND_NAMES` / `SKILL_DIRS` / `RETIRED_*` |
| `src/issue_flow/agent.py` | suggested next command strings; confirm marker path |
| `src/issue_flow/step_profiles.py` / config defaults | rename step key if needed |
| All templates that mention capture-`iflow-init` | dispatcher, pick, yolo, issue, fix, pause, workflow, rules prose |
| `tests/test_init.py`, consistency tests, any string pins | expect new names |
| `docs/issue-workflow.md` (via template), `docs/cli.md` if needed | document both commands |
| `.issueflows/04-designs-and-guides/iflow-init-vs-capture.md` | **new** |
| `HISTORY.md` | at close |

## Test strategy

- `uv run pytest`; `uv run ruff check src/ tests/`.
- Scaffold assertions: rendered tree has `iflow-<capture>` skill/command;
  `iflow-init` skill describes harness cold-start (not `agent capture`);
  no leftover "capture the GitHub issue" wording under `iflow-init`.
- `agent state` with no `*_original.md` suggests `/iflow-<capture>`, not
  cold-start init.
- `verify_scaffold.py` after rename.
- Retire prune: `issue-flow update` on a fixture that still has the old
  capture `iflow-init` folder removes it once the new cold-start is written
  (same pattern as `iflow-start` tests if any exist — extend or add).

## Open questions

1. **Capture-skill name?** **Locked: `iflow-capture`** (Accept A).
2. **Cold-start `/iflow-init` on-path or off-path?** **Locked: off-path.**
3. **Compat alias for one release?** **Locked: no.**
4. **Rename internal lifecycle stage id?** **Done:** `STAGE_CAPTURE = "capture"`; `STAGE_INIT` is a back-compat alias.
