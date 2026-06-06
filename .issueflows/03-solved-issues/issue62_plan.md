# Plan for issue #62: Make issue-flow editor-agnostic (Cursor, Claude Code, opencode, Codex)

## Goal
Let `issue-flow init` / `update` scaffold the workflow for AI coding tools beyond Cursor (Claude Code, opencode, Codex CLI) via an editor-profile abstraction, selectable with `--editor`. Skills + a shared `AGENTS.md` are the portable core; slash commands + `.mdc` / `CLAUDE.md` are per-editor extras.

## Decisions (confirmed with user)
- **Scope:** one PR for all three phases on this branch.
- **Rules target:** `AGENTS.md` for **every** editor, **plus** per-editor extras (`.cursor/rules/issueflow-rules.mdc` for Cursor, `CLAUDE.md` for Claude). opencode/Codex get `AGENTS.md` only.
- **Neutral naming allowed:** rename `docs/cursor-issue-workflow.md` -> `docs/issue-workflow.md` and de-Cursor shared wording for all editors (including Cursor). Accept a one-time orphan `cursor-issue-workflow.md` in already-initialized Cursor projects (`update` never deletes).
- **Default `editor=cursor`** for backward compat.

## Constraints
- `uv` only; Python 3.13+. Edit **templates** under `src/issue_flow/templates/`, never rendered copies.
- `AGENTS.md` is often a hand-maintained user file (this repo has one) -> must be written as a **marker-delimited managed block**, never a wholesale overwrite. `.mdc` / `CLAUDE.md` are issue-flow-owned and safe to overwrite.
- Keep one source of truth for the rules body so `.mdc` / `CLAUDE.md` / `AGENTS.md` never drift (shared Jinja partial via `{% include %}`).
- Minor defaults (no need to ask): opencode commands dir = `command/` (singular); `--editor` is repeatable and also accepts `all`.

### Prior art
- `_ensure_dotenv_file` (`issue_flow.init`) — convention: create-or-append a marked section (`_DOTENV_SECTION_HEADER`) without clobbering user content; new work: **mirror** this exact pattern for `_ensure_agents_md` (marker-delimited managed block, idempotent on init+update).
- `TEMPLATE_MANIFEST` + `resolve_output_path` (`issue_flow.templating`) — convention: `(template, "{placeholder}/path")` rendered via `str.format(**context)`; new work: **migrate** to `build_manifest(profile)` returning the same tuple shape, add `{commands_dir}` placeholder.
- `register_with_cursor` / `_graphify_postinstall` (`issue_flow.graphify`, `issue_flow.init`) — convention: best-effort, never raises; new work: **migrate** to `register_with_editor` gated on `profile.graphify_installer`.
- `Settings.template_context` (`issue_flow.config`) — convention: flat `dict[str,str]` context; new work: **coexist**, add `editor`, `editor_name`, `commands_dir`.

## Approach

### 1. Editor profiles (`src/issue_flow/editors.py`, new)
```python
@dataclass(frozen=True)
class EditorProfile:
    id: str
    name: str                       # display name (editor_name)
    agent_dir: str
    commands_dir: str | None        # None => no project slash commands (Codex)
    rules_extra: tuple[str, str] | None  # (template, output) for .mdc/CLAUDE.md; None otherwise
    graphify_installer: str | None  # "cursor" or None

EDITORS = {
  "cursor":   (...".cursor",   "commands", ("rules/issueflow-rules.mdc.j2","{agent_dir}/rules/issueflow-rules.mdc"), "cursor"),
  "claude":   (...".claude",   "commands", ("rules/CLAUDE.md.j2","CLAUDE.md"), None),
  "opencode": (...".opencode", "command",  None, None),
  "codex":    (...".codex",    None,       None, None),
}
```
Skills always emitted; `AGENTS.md` always emitted (managed block); docs always emitted (neutral name).

### 2. Config (`config.py`)
- Add `editor` (`ISSUEFLOW_EDITOR`, default `cursor`). Derive `agent_dir` from the profile **unless** `ISSUEFLOW_AGENT_DIR` is set explicitly.
- Extend `template_context()` with `editor`, `editor_name`, `commands_dir`.

### 3. Manifest (`templating.py`)
- Replace `TEMPLATE_MANIFEST` with `build_manifest(profile) -> list[tuple[str,str]]`: skills always; commands only when `commands_dir`; rules extra when present; docs (`{docs_dir}/issue-workflow.md`). `AGENTS.md` is handled by the init writer, not the manifest.
- Keep a module-level `TEMPLATE_MANIFEST = build_manifest(EDITORS["cursor"])` shim if convenient, or update callers/tests.

### 4. Templates (`src/issue_flow/templates/`)
- New `rules/_body.md.j2` = current rule body (no frontmatter), de-Cursored to generic "your agent" wording (e.g. the "Cursor's own LLM" line).
- `rules/issueflow-rules.mdc.j2` = frontmatter + `{% include "rules/_body.md.j2" %}`.
- New `rules/CLAUDE.md.j2` and `rules/AGENTS.md.j2` = heading + same include.
- Rename `docs/cursor-issue-workflow.md.j2` -> `docs/issue-workflow.md.j2`; neutralize "Cursor" wording (use `{{ editor_name }}` where an editor name is genuinely needed).
- Neutralize literal "Cursor" in `commands/graphify.md.j2` and `skills/issueflow_graphify/SKILL.md.j2` (and any other stray brand mentions found via grep). Deep per-editor command/skill divergence (e.g. Codex "use the skill, not the slash command") is noted but kept light this PR.

### 5. Init/update (`init.py`)
- `run_init` / `run_update` accept `editors: list[str]`; loop per profile, building a per-profile context (override `agent_dir`, `editor`, `editor_name`, `commands_dir`) and calling `_write_manifest_files(build_manifest(profile), ...)`.
- New `_ensure_agents_md(project_root, context, *, force)` — upsert a marker-delimited managed block into `AGENTS.md` (create if missing, replace between markers if present, append block if file exists without markers). Idempotent; called on both init and update.
- `_graphify_postinstall` takes the profile; only runs when `profile.graphify_installer`.
- `_already_initialized` uses `build_manifest(profile)`.
- `.env`: add `ISSUEFLOW_EDITOR` to `_DOTENV_KEYS`.

### 6. CLI (`cli.py`)
- Add `--editor` (repeatable `list[str]`, default `["cursor"]`, accepts `all`) to `init` and `update`; validate against `EDITORS`; pass through to `run_init` / `run_update`.

### 7. README
- Promote the "Multi-tool support" future-plan bullet into documented `--editor` usage and the per-editor output table.

## Files to touch
- `src/issue_flow/editors.py` — new profile registry.
- `src/issue_flow/config.py` — `editor` setting, profile-derived `agent_dir`, context additions.
- `src/issue_flow/templating.py` — `build_manifest(profile)`, `{commands_dir}` support.
- `src/issue_flow/init.py` — multi-editor loop, `_ensure_agents_md`, graphify gating, `_already_initialized`.
- `src/issue_flow/graphify.py` — `register_with_editor` gated on installer.
- `src/issue_flow/cli.py` — `--editor` option.
- `src/issue_flow/templates/rules/_body.md.j2` (new), `issueflow-rules.mdc.j2` (include), `CLAUDE.md.j2` (new), `AGENTS.md.j2` (new).
- `src/issue_flow/templates/docs/issue-workflow.md.j2` (renamed), `commands/graphify.md.j2`, `skills/issueflow_graphify/SKILL.md.j2` (de-Cursor).
- `README.md` — `--editor` docs.
- `tests/` — update doc-filename + manifest tests; add editor/profile, AGENTS.md managed-block, and graphify-rename tests.

## Test strategy
- `uv run pytest` and `uv run ruff check src/ tests/`.
- Update: `test_init_creates_docs` (-> `issue-workflow.md`), `test_manifest_entry_count` / manifest tests, graphify register tests (renamed fn).
- Add: per-editor `build_manifest` writes correct `agent_dir` / skills / rules file; Codex emits **no** commands dir; opencode uses `command/`; no `.cursor/` leakage and no literal "Cursor" in non-Cursor outputs; `AGENTS.md` managed block is created, refreshed in place, and preserves surrounding user content; `--editor all` and repeated `--editor` scaffold every selected tool.

## Open questions
- None blocking. (Multi-editor `AGENTS.md` resolved by keeping the body editor-neutral; deep Codex slash-command divergence intentionally deferred and noted.)
