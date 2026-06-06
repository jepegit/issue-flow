# Editor profiles (multi-tool scaffolding)

Context: issue #62 — make issue-flow able to scaffold for AI coding tools beyond
Cursor (Claude Code, opencode, Codex CLI).

## Decision

A single template tree is shared across editors; per-tool differences live in an
`EditorProfile` (`src/issue_flow/editors.py`). The `EDITORS` registry maps an
editor id to its `agent_dir`, `commands_dir` (or `None`), an optional
`rules_extra` `(template, output)`, and a `graphify_installer` (or `None`).
`build_manifest(profile)` (`templating.py`) turns a profile into the list of
templates to render; `run_init` / `run_update` loop once per selected profile.

Surfaces, by portability:

- **Skills** (`<agent_dir>/skills/<name>/SKILL.md`) — the portable core, emitted
  for every editor.
- **`AGENTS.md`** — the convergent rules target, emitted for every editor.
- **Slash commands** — only when the profile defines `commands_dir` (Codex has
  none; opencode uses singular `command/`).
- **Per-editor rules extra** — `.cursor/rules/issueflow-rules.mdc` (Cursor) and
  `CLAUDE.md` (Claude), layered on top of `AGENTS.md`.

## Key choices / alternatives

- **AGENTS.md as a managed block, not a manifest overwrite.** `AGENTS.md` is
  frequently hand-maintained, so `_ensure_agents_md` (`init.py`) only owns the
  content between `<!-- BEGIN/END issue-flow ... -->` markers (mirrors the
  existing `_ensure_dotenv_file` pattern). Create / refresh-in-place / append;
  never clobbers user content. This is why it is *not* in `build_manifest`.
- **One rules body source of truth.** `templates/rules/_body.md.j2` is included
  by the `.mdc`, `CLAUDE.md.j2`, and `AGENTS.md.j2` templates so the three never
  drift. The body is intentionally editor-neutral (no `editor_name`) so the
  shared `AGENTS.md` content is identical across editors (no churn when several
  editors are selected).
- **Backward compatibility.** Default `editor=cursor`; `ISSUEFLOW_AGENT_DIR`
  still overrides `agent_dir` when set explicitly, otherwise it is derived from
  the profile. The only deliberate change to Cursor output is the rename
  `docs/cursor-issue-workflow.md` → `docs/issue-workflow.md` plus the new shared
  `AGENTS.md`.
- **De-Cursoring.** Brand wording uses `{{ editor_name }}`; graphify
  registration text is gated on `{{ graphify_installer }}`. Tests assert no
  literal "Cursor" leaks into non-Cursor outputs.
- **Rejected:** separate per-editor template trees (too much duplication).

## Deferred

Deep per-editor command/skill divergence for Codex (slash-command-free phrasing
beyond the shared note) is intentionally out of scope; skills + `AGENTS.md` are
the portable contract.
