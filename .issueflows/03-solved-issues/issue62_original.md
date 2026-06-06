# Issue #62: Make issue-flow editor-agnostic (Cursor, Claude Code, opencode, Codex)

Source: https://github.com/jepegit/issue-flow/issues/62

## Original issue text

## Summary

Make issue-flow able to scaffold its workflow for AI coding tools other than Cursor. Concrete near-term targets: **Claude Code**, **opencode**, and **Codex CLI**. This was listed under "Future plans" in the README ("Multi-tool support — generate config for other AI coding tools (Claude Code, Windsurf, etc.)").

## Where we stand today

The architecture is already most of the way there: issue-flow is a template renderer (`TEMPLATE_MANIFEST` in `templating.py` maps Jinja templates -> output paths), and every output path is parameterized on `{agent_dir}` (configurable via `ISSUEFLOW_AGENT_DIR`, default `.cursor`). There's even a deprecation shim for the old `ISSUEFLOW_CURSOR_DIR`.

What's actually Cursor-locked:
- Agent dir defaults to `.cursor/` (already just `agent_dir`).
- Hardcoded "Cursor" wording in templates (`docs/cursor-issue-workflow.md.j2`, the `.mdc` rule, `iflow.md.j2`, "Cursor's own LLM cannot be reused by subprocesses", etc.).
- graphify integration runs `graphify cursor install` (`register_with_cursor` in `graphify.py`/`init.py`).
- The always-on rule is a Cursor `.mdc` (frontmatter `globs`/`alwaysApply`).

## How the target tools line up (verified 2026)

| Concern | Cursor | Claude Code | opencode | Codex CLI |
|---|---|---|---|---|
| Agent dir | `.cursor/` | `.claude/` | `.opencode/` | `.codex/` (+ `.agent/`) |
| Slash commands | `commands/*.md` | `commands/*.md` | `command/` or `commands/*.md` (`$ARGUMENTS`/`$1`/`$NAME`, frontmatter `description`/`agent`) | **removed in v0.117.0** — no project slash commands |
| Skills (`SKILL.md`) | yes | yes | yes (`skills/`) | yes (`.codex/skills` / `.agent/skills`, project-scoped) |
| Rules / memory | `.cursor/rules/*.mdc` | `CLAUDE.md` | `AGENTS.md` (+ `instructions` glob in `opencode.json`) | `AGENTS.md` |

### Two findings that reshape the design

1. **Skills are the real convergence point.** All four tools support the same Agent Skills `SKILL.md` format under `<agent_dir>/skills/<name>/`. issue-flow already ships every command as a skill, so that surface ports to all four with nothing but a different `agent_dir`. This is the robust core.
2. **AGENTS.md is the convergent rules target.** Codex and opencode both standardize on `AGENTS.md`; Cursor and Claude read it natively too. So `AGENTS.md` is arguably the best *default* rules output, with `.mdc`/`CLAUDE.md` as optional per-editor extras.

### Codex is a partial case

Codex CLI removed project-scoped custom prompts/slash commands in v0.117.0 (official guidance: convert prompts -> skills). So on Codex you get **skills + AGENTS.md but no `/issue-init`-style slash commands** — users invoke `issueflow-issue-init` (skill) instead of `/issue-init`. That's acceptable because issue-flow already mirrors every command as a skill.

Honest framing: **skills + AGENTS.md are the portable core; slash commands + `.mdc` are Cursor/Claude/opencode niceties.**

## Proposed approach: editor profiles

Introduce a small editor-profile abstraction instead of duplicating template trees.

- New `src/issue_flow/editors.py` with an `EditorProfile` and an `EDITORS` registry (`cursor`, `claude`, `opencode`, `codex`). Suggested fields:
  - `id`, `name`, `agent_dir`
  - `commands_dir: str | None` — `None` for Codex (no project commands); opencode accepts singular `command/` or plural `commands/`
  - `skills_supported: bool` — `True` for all four (the reliable surface)
  - `rules_template` + `rules_output` — `.cursor/rules/issueflow-rules.mdc` | `CLAUDE.md` | `AGENTS.md`
  - `graphify_installer: str | None` — `"cursor"` for Cursor, `None` for the rest
- `config.py`: add `editor` setting (`ISSUEFLOW_EDITOR`, default `cursor` for backward compat); derive `agent_dir` from the profile unless `ISSUEFLOW_AGENT_DIR` is set explicitly; extend `template_context()` with `editor`, `editor_name`, etc.
- `templating.py`: turn `TEMPLATE_MANIFEST` into `build_manifest(profile)` — skills always; commands only when `commands_dir` is set; rules entry from the profile; rename `docs/cursor-issue-workflow.md.j2` -> editor-neutral `docs/issue-workflow.md.j2`.
- `cli.py`: add `--editor [cursor|claude|opencode|codex]` (multi-select) to `init`/`update`; loop the scaffold once per selected profile.
- Templates: add `templates/rules/CLAUDE.md.j2` and `templates/rules/AGENTS.md.j2`, sharing one body via a `{% include %}` partial so `.mdc` / `CLAUDE.md` / `AGENTS.md` never drift; neutralize "Cursor" wording with `{{ editor_name }}` / `{{ agent_dir }}`.
- graphify: gate `register_with_cursor` on `profile.graphify_installer`; rename to `register_with_editor`; skip cleanly when a profile has no installer.
- README: promote the future-plan bullet into documented `--editor` usage.

### Alternatives considered
- Separate template trees per editor (`templates/cursor/`, `templates/claude/`) — too much duplication. Rejected.
- AGENTS.md-only convergence (one root file all tools read) — now looks like the best *default* rather than just an option (see findings above).

## Open questions
1. Default rules target: per-editor (`.mdc` / `CLAUDE.md` / `AGENTS.md`) vs **AGENTS.md for everyone** (now the leading candidate). Likely: AGENTS.md as the shared backbone, `.mdc`/`CLAUDE.md` as opt-in extras.
2. Multi-editor selection UX: `--editor both/all` vs repeatable `--editor cursor --editor claude`.
3. opencode commands dir: emit `command/` or `commands/`? (Both supported; pick one for consistency.)
4. Keep default `editor=cursor` so existing installs are byte-for-byte unchanged (assumed yes).

## Suggested phasing
1. Profiles + config + manifest refactor; Cursor output unchanged (golden tests still pass byte-for-byte).
2. Claude + opencode + Codex profiles; `CLAUDE.md.j2` / `AGENTS.md.j2` + shared rules partial; de-Cursored wording.
3. CLI `--editor`, multi-editor loop, graphify gating, README.

Tests: assert each `--editor X` writes the right `agent_dir`, skills, and rules file; assert Codex emits no `commands/`; assert no `.cursor/` leakage and no literal "Cursor" in non-Cursor outputs.
