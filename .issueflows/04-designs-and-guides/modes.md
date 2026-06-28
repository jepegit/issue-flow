# Scaffolding modes

Context: issue #48 — let users pick which workflow surfaces `issue-flow init`
installs (e.g. a lightweight markdown-only workflow), and make it extensible so
developers can ship new modes and users can define custom ones.

## Decision

A **mode** is a named selection of workflow surfaces (skill stems from
`SKILL_DIRS`, command stems from `COMMAND_NAMES`). Modes are **data-driven**:

- Built-in modes ship as packaged data in
  [`src/issue_flow/modes.toml`](../../src/issue_flow/modes.toml) (`standard` =
  everything, back-compat default; `simple` = markdown-only lifecycle).
- A project may add or override modes in its own `.issueflows/config.toml` using
  the same `[modes.<id>]` grammar. Project tables win on id clash.
- `src/issue_flow/modes.py` mirrors the `editors.py` pattern: a frozen `Mode`
  dataclass + a resolver (`resolve_mode`) that expands the `all` sentinel and the
  `extends` / `add` / `remove` composition keys into concrete, validated stem
  sets. A mode may only reference stems that ship as packaged templates.

The **active** mode for a project is persisted to `.issueflows/config.toml`
`[issueflow].mode` (committed, so `update` honours it after a fresh checkout —
unlike `.env`, which is git-ignored). Resolution order: **`--mode` (CLI, applied
by `run_init` before the fallback resolver) > persisted `config.toml` >
`ISSUEFLOW_MODE` env > `DEFAULT_MODE` ("standard")**. The persisted choice
deliberately beats the environment so a stray `ISSUEFLOW_MODE` cannot silently
override the project's mode on `update` (honouring the issue contract: switching
modes is an `init --mode` action). `init --mode <id>` is the only way to change
it; `update` reads but never writes it.

## Two structural choices (and why)

These make the system ready for future surfaces/modes without per-mode `if`
ladders (the scenarios that motivated the design):

- **A. Templates gate on surface *membership*, not mode id.** The render context
  carries `included_skills` / `included_commands` (sorted stem lists). Templates
  branch with `{% if "iflow_close" in included_skills %}` etc. A new surface
  (e.g. a hypothetical `caveman` or a `grill_me` sub-skill used by `iflow-plan`)
  is gated by its own membership, so any current/future mode that includes it
  lights it up — no enumeration of mode names. For `standard` the set is "all",
  so output is unchanged.
- **B. Mode definitions are data, mergeable from project config.** This is what
  lets a user define a custom mode (`extends = "simple"`, `add = ["grill_me"]`)
  without editing package source, and keeps "what each mode contains" editable.

## Mechanics

- `build_manifest(profile, mode=None)` filters command/skill entries by the
  mode's stem sets. `mode=None` keeps the full set (back-compat for existing
  call sites / `TEMPLATE_MANIFEST`). Rules extra, the workflow doc, and the
  `AGENTS.md` block are emitted for every mode; their *content* adapts via
  membership gating.
- `init` / `update` resolve the active `Mode` once and thread it through
  `build_manifest` and `template_context`, then call
  `_prune_excluded_surfaces(...)` to delete previously-scaffolded skills/commands
  the active mode excludes (so a `standard -> simple` switch actually shrinks the
  surface and `update` stays idempotent). Only issue-flow's own generated
  surfaces are pruned; user files are untouched.
- Persistence round-trips via `tomlkit` so updating `[issueflow].mode` preserves
  user comments and `[modes.*]` tables.

## Scope / deferred

- `simple` is a *subset selection*; individual skills are not rewritten per mode.
  The `iflow` dispatcher's done-state is membership-gated (no `/iflow-close` route
  when close isn't installed; it points at moving files to `03-solved-issues/`
  instead), and the workflow doc prints a mode banner listing the installed
  surfaces. Deeper per-mode rewording of individual skills (e.g. a no-PR `close`
  variant) is intentionally deferred — the mode *mechanism* is the deliverable.

## Rejected

- `.env`-only persistence (git-ignored → lost on checkout, `update` couldn't
  honor it).
- A hardcoded Python `MODES` dict only (would block user-defined custom modes,
  which scenario testing for #48 explicitly required).
