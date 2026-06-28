# Issue #48 status: Create options for issue-flow modes

- [x] Done

## Summary

Added a data-driven **mode** system to issue-flow. `issue-flow init --mode
<id>` selects which workflow surfaces are scaffolded; the choice is persisted to
`.issueflows/config.toml` and honoured by `issue-flow update` (which never
changes the mode). Built-in modes: `standard` (full, default, back-compat) and
`simple` (markdown-only lifecycle). Projects can define custom modes in
`.issueflows/config.toml`.

## What landed

- **`src/issue_flow/modes.py`** (new) — `Mode` dataclass, registry
  loader/merger (built-in + project `config.toml`), `resolve_mode`,
  `available_modes`, stem validation, `all`/`extends`/`add`/`remove` expansion,
  and active-mode read/write (tomlkit round-trip).
- **`src/issue_flow/modes.toml`** (new, packaged) — built-in `standard` + `simple`.
- **`templating.py`** — `build_manifest(profile, mode=None)` filters surfaces by
  mode (None ⇒ full set, back-compat); added `skill_output_name` helper.
- **`config.py`** — `resolve_active_mode_id` / `resolve_mode` / `config_path`;
  `template_context` now carries `mode`, `mode_name`, `included_skills`,
  `included_commands`. Resolution order: **`--mode` (CLI, on `init`) > persisted
  `config.toml` > `ISSUEFLOW_MODE` env > `standard`** — the persisted choice
  beats the env so a stray `ISSUEFLOW_MODE` can't override the project's mode on
  `update`.
- **`init.py`** — `run_init(..., mode=...)` validates + persists the mode;
  `run_update` reads the persisted mode; both thread it through and call
  `_prune_excluded_surfaces` to drop surfaces the active mode excludes; added
  `ISSUEFLOW_MODE` to the `.env` hints.
- **`cli.py`** — `--mode/-m` on `init` only (`update` has no mode flag).
- **Templates** — `iflow` dispatcher done-state is membership-gated (no
  `/iflow-close` route in `simple`); workflow doc prints a mode banner when not
  `standard`. Gating uses surface membership (`included_skills`), not mode id.
- **Dependency** — added `tomlkit`.
- **Docs** — `README.md` (Modes section + option table), `docs/developing.md`
  (Scaffolding modes section + structure), design note
  `.issueflows/04-designs-and-guides/modes.md`.

## Tests

- New `tests/test_modes.py` (registry, resolution, custom-mode merge,
  extends/add/remove, circular-extends, persistence round-trip, env override).
- Extended `test_init.py`, `test_update.py`, `test_cli.py`, `test_config.py`,
  `test_templating.py`.
- `uv run pytest` → **188 passed**; `uv run ruff check src/ tests/` → clean.
- Manual e2e: `init --mode simple` (subset + config.toml), `update` (honors
  mode), custom `[modes.mine]` extends simple + adds graphify (scenario #3),
  switch back to `standard` (restores full set).

## Future-scenario readiness (the stress test that shaped the design)

- **New mode adding a new skill (e.g. CAVEMAN) + AGENTS.md text** — add the
  skill template + stem; define the mode (`extends`/`add`); gate the AGENTS.md
  block on `{% if "caveman" in included_skills %}`. Enabled now (context var
  present).
- **New sub-skill used by a step (e.g. GRILL-ME in iflow-plan), part of a mode**
  — same membership-gating pattern in the `iflow_plan` template. Enabled now.
- **Custom mode for a surface in no built-in mode** — user `[modes.*]` in
  `.issueflows/config.toml`. Working (verified e2e).

## Remaining / deferred

- Deeper per-mode rewording of individual skills (e.g. a no-PR `close` variant
  for `simple`) is intentionally deferred; this issue delivers the mode
  *mechanism* + a sensible `simple` subset. Recorded in the design note.
