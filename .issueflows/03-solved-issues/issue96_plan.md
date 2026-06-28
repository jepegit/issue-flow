# Issue #96 plan — `issue-flow config` command

## Goal

Add a CLI command that **creates** `.issueflows/config.toml` (if missing),
pre-populated from `.env`/env values where set and issue-flow defaults
otherwise, then prints how to hand-edit it later. Live under its own `config`
namespace (`issue-flow config add`, per the issue).

## Constraints

- **Templates are source of truth** for scaffolded *target-project* files — but
  this is a change to the **tool's own CLI** (`src/issue_flow/`), not a template.
- `config.toml` round-trips must use **`tomlkit`** (comment-preserving), matching
  `modes.write_active_mode`. Reads elsewhere use stdlib `tomllib`.
- **Don't clobber** an existing `config.toml` silently — `init --mode` and
  `write_active_mode` already create/merge it. Default to no-op-if-present unless
  `--force`, and never drop user comments / `[modes.*]` tables.
- Honor documented precedence: a created file's values come from
  env/`.env` if set, else issue-flow defaults (the file itself is the layer being
  written, so env is the only fallback to read here).
- Python 3.13+, Typer, `uv run` for everything.

### Prior art

- `modes.write_active_mode(cfg_path, mode_id)` (`src/issue_flow/modes.py`) —
  already creates `config.toml` with a header comment and upserts
  `[issueflow].mode` via tomlkit. **Reuse/extend** this rather than a new writer.
- `modes.read_active_mode` / `read_caveman_default` / `read_grill_me_default` —
  the only keys issue-flow actually reads from `config.toml`'s `[issueflow]`.
- `Settings.resolve_active_mode_id` / `resolve_caveman_default` /
  `resolve_grill_me_default` (`config.py`) — encode env→default fallback; reuse to
  compute the values to write (with `config.toml` absent they fall straight
  through to env→default, exactly what we want).
- `agent.py` `run_*` orchestrators — Console + optional `--json` + exit-code
  pattern + `_emit_json`; mirror it for the new command.
- `init.py` (~L344-350) writes `config.toml` only when `--mode` is explicit, so a
  dedicated command to materialize a full, commented file is genuinely useful.

## Approach

1. **Scope of keys (recommended):** write the `[issueflow]` table with the three
   keys issue-flow actually reads from `config.toml`:
   - `mode` ← `ISSUEFLOW_MODE` (env/`.env`) else `DEFAULT_MODE` (`"standard"`).
   - `caveman_default` ← `ISSUEFLOW_CAVEMAN_DEFAULT` else `false`.
   - `grill_me_default` ← `ISSUEFLOW_GRILL_ME_DEFAULT` else `false`.
   The other `ISSUEFLOW_*` vars (`DIR`, `EDITOR`, `AGENT_DIR`, `DOCS_DIR`,
   `HISTORY_FILE`) are **env-only by design** — issue-flow never reads them from
   `config.toml`, so writing them there would produce a config that lies. (See
   open question.)
2. **Writer helper** in `modes.py`, e.g.
   `write_default_config(cfg_path, *, mode, caveman_default, grill_me_default, overwrite=False)`:
   - If file exists and not `overwrite`: return a "exists" result, write nothing.
   - Else build a tomlkit doc with a header comment + per-key explanatory inline
     comments (what each does, accepted values, that caveman/grill need
     `issue-flow update` to re-render the rule body), write the `[issueflow]`
     table. When the file already exists with `overwrite`, parse + upsert the
     three keys (preserve other content) rather than blowing the file away.
3. **Orchestrator** `run_config_add(project_root, console, force, as_json)` in
   `agent.py` (reuses `Settings`, `_emit_json`, exit-code convention):
   - Compute values via the `Settings.resolve_*` helpers.
   - Call the writer; on "exists" print a yellow note + the manual-edit hint and
     return non-zero (mirror `capture`'s exists path), unless `--force`.
   - On success: green `wrote <path>`, then print the **manual-edit guide**
     (path, the three keys + accepted values, env-var fallbacks, and the
     `issue-flow update` reminder for caveman/grill).
4. **CLI wiring** in `cli.py`: new `config_app = typer.Typer(name="config")` with
   an `add` command (`--project-dir/-C`, `--force/-f`, `--json`), then
   `app.add_typer(config_app)`. Mirror `agent_capture`'s option style.

## Files to touch

- `src/issue_flow/modes.py` — add `write_default_config` (+ small shared helper
  for the commented `[issueflow]` table; optionally refactor `write_active_mode`'s
  header-comment creation to share).
- `src/issue_flow/agent.py` — add `run_config_add` orchestrator (+ the
  manual-edit guide text).
- `src/issue_flow/cli.py` — add `config` Typer sub-app + `add` command.
- `tests/test_cli.py` — CliRunner tests (see below).
- `README.md` — document `issue-flow config add` in the Configuration section.
- `HISTORY.md` — changelog entry (at `/iflow-close`).

## Test strategy

`uv run pytest` (+ `uv run ruff check src/ tests/`). New tests in
`tests/test_cli.py` using `CliRunner` in a tmp project:

- Creates `.issueflows/config.toml` with the three keys at defaults when no env
  set; TOML parses; `read_active_mode`/`read_caveman_default`/`read_grill_me_default`
  round-trip the written values.
- Env-derived values: with `ISSUEFLOW_MODE=simple` /
  `ISSUEFLOW_CAVEMAN_DEFAULT=true` set, the written file reflects them.
- Idempotency: second run without `--force` does **not** clobber (exit non-zero /
  "exists" message), and preserves a hand-added comment / `[modes.*]` table.
- `--force` upserts the three keys while preserving other content.
- `--json` emits a stable payload (`written`, `path`, values).

## Decisions (resolved)

1. **Key scope** — write **only the three config-driven toggles** (`mode`,
   `caveman_default`, `grill_me_default`). The env-only vars are *not* written
   (not even as commented hints), keeping the file honest.
2. **Subcommand verb** — `issue-flow config add` (as the issue requests).
3. **Orchestrator home** — `agent.py`, reusing the `run_*` / `_emit_json` /
   exit-code pattern (its docstring's "CLI orchestrators" framing covers it).
