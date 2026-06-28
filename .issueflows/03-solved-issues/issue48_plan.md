# Issue #48 plan: Create options for issue-flow modes

## Goal

Let users pick an issue-flow **mode** at `init` time (`issue-flow init --mode simple`)
that controls which workflow surfaces (skills/commands) get scaffolded. Persist
the chosen mode so `issue-flow update` refreshes exactly that mode's surfaces, and
changing mode requires re-running `init`. Make modes **config-driven data** so
developers can ship new built-in modes and users can define **custom modes** in
their project, without source edits.

## Constraints

- **Back-compat:** the default mode (`standard`) must reproduce today's full
  scaffold exactly. No behavior change for users who don't pass `--mode`.
- `update` must **respect the persisted mode** and must **not** grow a `--mode`
  flag — switching modes is an `init`-only action (per the issue).
- Issue markdown under `.issueflows/` is never written/deleted by the manifest
  (`tests/test_update.py::test_update_preserves_issue_markdown`).
- Mirror the existing extensibility patterns (`editors.py` registry,
  `build_manifest(profile)`); don't invent a parallel style.
- A custom/built-in mode may only reference surface stems that **exist as packaged
  templates** — validate and fail fast otherwise (you can't scaffold a template
  that isn't shipped).
- `uv`-only toolchain; Python 3.13; keep `ruff` clean.

### Prior art

- `src/issue_flow/editors.py` — `EditorProfile` + `EDITORS` registry + `get_profile`
  / `resolve_editors`. The `Mode` dataclass + resolver mirror this shape.
- `src/issue_flow/templating.py` — `COMMAND_NAMES`, `SKILL_DIRS`,
  `build_manifest(profile)`, `SKILL_OUTPUT_NAMES`. The canonical stem lists; the
  manifest is the natural filter point. (grep: `build_manifest`, `SKILL_DIRS`.)
- `src/issue_flow/config.py` — `Settings` reads `ISSUEFLOW_*` env/`.env`, builds
  `template_context`. Mode + included-surface sets join the context here.
- `src/issue_flow/init.py` — `_ensure_dotenv_file` (managed-file upsert pattern),
  `_ensure_agents_md` (marker-block round-trip), `_prune_retired_files` /
  `_prune_command_files` (surface pruning), `_create_issueflow_dirs`. Mode
  persistence + "prune surfaces excluded by the active mode" plug in here.
- `RETIRED_COMMANDS` / `RETIRED_SKILLS` pruning — same machinery reused to remove
  surfaces a narrower mode (or a mode switch) excludes.

## Design decisions (drives the three future scenarios)

Two structural choices make this ready for "new mode adds CAVEMAN", "GRILL-ME sub-skill
in a mode", and "user-defined custom mode" (see Scenario coverage below):

- **A. Templates gate on surface *membership*, not mode id.** The render context
  carries the resolved `included_skills` / `included_commands` sets, so any
  template branches like `{% if "grill_me" in included_skills %}` / `{% if
  "caveman" in included_skills %}`. No per-mode `if mode == ...` ladders; AGENTS.md,
  the dispatcher, and sub-skill references describe exactly the surfaces present.
  For `standard` the set is "all", so every conditional is true and output is
  byte-for-byte identical to today.
- **B. Mode definitions are data, mergeable from a project config file.** Built-in
  modes ship as packaged data; a project `.issueflows/config.toml` can add new
  modes or override built-ins, and also stores the active mode. This is the
  issue's own hint ("configuration files where we specify what each mode
  contains") and is what unlocks custom modes.

## Approach

**1. Mode model + built-ins (`src/issue_flow/modes.py` + `src/issue_flow/modes.toml`).**

```python
@dataclass(frozen=True)
class Mode:
    id: str
    name: str
    description: str
    skills: frozenset[str]      # concrete, resolved subset of SKILL_DIRS
    commands: frozenset[str]    # concrete, resolved subset of COMMAND_NAMES

DEFAULT_MODE = "standard"
```

Built-in modes live in a packaged `modes.toml` (read via `importlib.resources` +
stdlib `tomllib`) so "what each mode contains" is editable config, not buried in
code. A sentinel like `skills = "all"` expands to the full `SKILL_DIRS`. Optional
`extends = "<mode>"` plus `add` / `remove` lists keep definitions terse (e.g.
`ife = standard + caveman`).

```toml
[modes.standard]
name = "Standard"
skills = "all"
commands = "all"

[modes.simple]
name = "Simple"
skills = ["iflow", "iflow_init", "iflow_comments", "iflow_plan",
          "iflow_start", "iflow_pause", "iflow_status"]
commands = ["iflow", "iflow-init", "iflow-plan", "iflow-start",
            "iflow-pause", "iflow-status"]
```

Proposed **simple** = markdown lifecycle only (no git/PR automation): excludes
`iflow_pick`, `iflow_close`, `iflow_cleanup`, `iflow_yolo`, `iflow_fix`,
`iflow_version_bump`, `iflow_history_update`, `iflow_graphify`. Moving issues to
`02-`/`03-` still works (`iflow-pause` parks to `02-`; the init/start archive
sweep routes done issues to `03-`). (See Open questions for the exact list.)

**2. Mode resolution + project overrides (`modes.py`).** A loader merges built-in
`modes.toml` with the project's `.issueflows/config.toml` `[modes.*]` tables
(project wins on id clash; new ids are added). `resolve_mode(project_root,
mode_id)` validates the id against the merged registry and validates every stem
against `SKILL_DIRS` / `COMMAND_NAMES` (unknown stem -> `ValueError` listing valid
stems). Returns a fully-resolved `Mode` (sets concrete after `all`/`extends`).

**3. Active-mode persistence in `.issueflows/config.toml`.** A small
`[issueflow]` table holds `mode = "simple"`. Writing preserves user content and
custom `[modes.*]` tables (use `tomlkit` for round-trip; add as a dependency via
`uv add tomlkit`). The file is committed (under `.issueflows/`), so `update` honors
the mode after a fresh checkout — unlike `.env`, which is git-ignored
(see `.gitignore`). Active-mode resolution order: `ISSUEFLOW_MODE` env/`.env` >
`.issueflows/config.toml [issueflow].mode` > `DEFAULT_MODE`.

**4. Manifest filtering (`templating.py`).** `build_manifest(profile, mode)` keeps
only command/skill entries whose stem is in the resolved mode sets. `rules_extra`,
`DOCS_ENTRY`, and the `AGENTS.md` block are emitted for every mode (their *content*
adapts via membership gating, decision A). Back-compat shim: `mode=None` resolves
to `standard` so existing call sites (`_already_initialized`, `TEMPLATE_MANIFEST`)
keep working.

**5. `Settings` + context (`config.py`).** Resolve the active mode and add `mode`,
`mode_name`, `included_skills`, `included_commands` to `template_context`
(skill membership keyed by the underscore stems used in `SKILL_DIRS`).

**6. CLI (`cli.py`).** Add `--mode/-m <id>` to `init` only (free-form string,
validated at runtime against the merged registry so custom modes are accepted;
error lists known modes). On `init`: if `--mode` given, persist it to
`config.toml`; if omitted, keep the existing persisted mode (else `standard`) —
never silently downgrade. `update` gains no flag; `run_update` reads the persisted
mode.

**7. Prune surfaces excluded by the active mode (`init.py`).** After writing, remove
previously-scaffolded skills/commands not in the active mode (reuse
`_prune_command_files` + the skill-folder prune loop, fed by "all known stems
minus active-mode stems"). Makes standard->simple actually shrink, and keeps
`update` idempotent. Never touches issue markdown or user files.

**8. Membership-gated template wording.** Update the dispatcher
(`templates/skills/iflow_iflow/SKILL.md.j2`), rules body
(`templates/rules/_body.md.j2`), and workflow doc
(`templates/docs/issue-workflow.md.j2`) to gate lifecycle/surface mentions on
`included_skills`. Sub-skill references (e.g. `iflow_init` -> `iflow_comments`,
and future `iflow_plan` -> `grill_me`) are gated the same way. Standard output
stays identical.

## Scenario coverage (the stress test)

- **(1) New `ife` mode = current + CAVEMAN, CAVEMAN text in AGENTS.md.** Add
  `caveman` template + stem; define `[modes.ife]` as `extends = "standard"`,
  `add = ["caveman"]`. AGENTS.md body wraps CAVEMAN guidance in
  `{% if "caveman" in included_skills %}`. No conditional ladders.
- **(2) GRILL-ME sub-skill used in the plan step, part of `ife`.** Add `grill_me`
  template + stem; include it in `ife`. `iflow_plan` template references it via
  `{% if "grill_me" in included_skills %}`. Works for any mode that includes it.
- **(3) GRILL-ME in no built-in mode; user wants a custom mode.** User adds to
  `.issueflows/config.toml`: `[modes.mine] extends = "standard"`,
  `add = ["grill_me"]`, and `[issueflow] mode = "mine"` (or `init --mode mine`).
  The loader merges it; validation passes because `grill_me` is a packaged stem.

## Files to touch

- `src/issue_flow/modes.py` (**new**) — `Mode`, loader/merger, `resolve_mode`,
  `DEFAULT_MODE`, stem validation, `all`/`extends`/`add`/`remove` expansion.
- `src/issue_flow/modes.toml` (**new, packaged**) — built-in `standard` + `simple`.
- `src/issue_flow/templating.py` — `build_manifest(profile, mode=None)` filtering;
  helper exposing known stems + per-mode included/excluded sets for pruning.
- `src/issue_flow/config.py` — read `.issueflows/config.toml`, resolve active mode,
  add `mode` / `mode_name` / `included_skills` / `included_commands` to context.
- `src/issue_flow/init.py` — write/read `[issueflow].mode` (tomlkit round-trip);
  thread mode through manifest; prune mode-excluded surfaces; ensure config.toml.
- `src/issue_flow/cli.py` — `--mode/-m` on `init`; `update` unchanged externally.
- `templates/skills/iflow_iflow/SKILL.md.j2`, `templates/rules/_body.md.j2`,
  `templates/docs/issue-workflow.md.j2` (+ any sub-skill refs) — membership gating.
- `pyproject.toml` — add `tomlkit`.
- `tests/test_modes.py` (**new**) + updates to `test_init.py`, `test_update.py`,
  `test_templating.py`, `test_config.py`, `test_cli.py`.
- Docs: `readme.md` / `docs/developing.md` + `.env` hint (`ISSUEFLOW_MODE`).
- `.issueflows/04-designs-and-guides/modes.md` (**new**) — durable design note
  (decisions A and B, scenario coverage).

## Test strategy

Run `uv run pytest` and `uv run ruff check src/ tests/`.

- **Modes:** built-ins load; `all`/`extends`/`add`/`remove` expand correctly;
  unknown mode id and unknown stem both raise helpful errors; project
  `config.toml` `[modes.*]` merges/overrides; custom mode referencing a real but
  mode-less stem (the GRILL-ME case) resolves.
- **Manifest:** `build_manifest(profile, standard)` == today's manifest
  (back-compat); simple omits excluded stems, keeps rules/docs/AGENTS.
- **Persistence:** `init --mode simple` writes `[issueflow].mode`; re-`init`
  without `--mode` keeps it; user `[modes.*]` survives the write (round-trip);
  env `ISSUEFLOW_MODE` overrides the file.
- **init/update:** `--mode simple` scaffolds only the subset and prunes excluded
  surfaces when switching from standard; `update` honors the persisted mode and
  does not re-create excluded skills; default (no config) still yields full
  standard; existing `test_update_*` invariants pass.
- **Templates:** membership gating — standard output unchanged; a synthetic mode
  excluding a stem drops its mention; including an extra stem surfaces it.
- **cli:** `init --mode bogus` exits non-zero with known-modes message; `update`
  has no `--mode`.

## Open questions

1. **Exact simple-mode surface set.** Confirm the proposed include list (init,
   comments, plan, start, pause, status, iflow); should simple also keep
   `iflow-pick` and/or a stripped "finish" step?
2. **`tomlkit` dependency OK?** Needed for comment/formatting-preserving writes to
   `.issueflows/config.toml`. Alternative: stdlib `tomllib` read + `tomli-w`
   write (loses comments/formatting), or hand-managed `[issueflow]` section.
3. **Custom-mode definition syntax.** OK with `extends` + `add`/`remove` (plus
   explicit `skills`/`commands`) as the config grammar, or prefer explicit lists
   only?
```
