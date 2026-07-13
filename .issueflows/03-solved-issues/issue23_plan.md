# Issue #23 — plan

## Goal

Let mixed-editor teams share one repo: commit a **canonical issue-flow agent layout**, let each developer materialize their local editor surfaces (Cursor, Claude Code, opencode, Codex) on demand, and (in a follow-up) automate pull/push conversion via opt-in git hooks.

## Constraints

- **Back-compat:** `issue-flow init` / `update` with `--editor cursor` (default) must behave as today for solo developers who do not opt into conversion.
- **Portable core already exists:** skills (`SKILL.md`) + `AGENTS.md` managed block + `.issueflows/` tree are editor-neutral per [editor-profiles.md](../04-designs-and-guides/editor-profiles.md).
- **No silent hook installs:** graphify precedent ([graphify-integration.md](../04-designs-and-guides/graphify-integration.md)) — hooks are opt-in, user-confirmed, documented. Overlaps with #101 (issue-file moves) but different purpose; keep hook scripts composable.
- **Templates stay source of truth:** canonical files are rendered from packaged Jinja2 templates, not hand-edited copies that drift from `update`.
- **Scope limit this PR:** Phase 1 only (canonical format + refactor + `convert` CLI + docs). Git hooks land Phase 2 unless you explicitly want one large PR.

### Prior art

| Hit | Module / doc | Relevance |
|-----|--------------|-----------|
| `EditorProfile`, `EDITORS`, `resolve_editors()` | [`src/issue_flow/editors.py`](../../src/issue_flow/editors.py) | Registry of per-editor paths and surfaces — extend, don't duplicate. |
| `build_manifest()`, `render_template()` | [`src/issue_flow/templating.py`](../../src/issue_flow/templating.py) | Manifest + render loop shared by init/update. |
| `run_init()`, `run_update()`, `_write_manifest_files()` | [`src/issue_flow/init.py`](../../src/issue_flow/init.py) | Scaffold loop to extract into reusable `apply_profile()` / `materialize_surfaces()`. |
| `Settings.template_context()` | [`src/issue_flow/config.py`](../../src/issue_flow/config.py) | Editor/mode/skill_level context for rendering. |
| `verify_scaffold.py` | [`.issueflows/00-tools/verify_scaffold.py`](../00-tools/verify_scaffold.py) | Multi-editor init smoke — extend for `convert`. |
| [editor-profiles.md](../04-designs-and-guides/editor-profiles.md) | design | Skills-first portable core; per-editor extras (`.mdc`, `CLAUDE.md`, commands). |
| [multi-repo-workspaces.md](../04-designs-and-guides/multi-repo-workspaces.md) | design | Workspace registry orthogonal; conversion is per-repo. |
| Agent Skills open standard | [agentskills.io](https://agentskills.io) / Cursor docs | Portable `SKILL.md` format; `.agents/skills/` is cross-tool but issue-flow already emits per-editor `agent_dir/skills/`. |
| #101, #17 | GitHub | #101 = issue-file hook moves; #17 = Windsurf editor profile (out of scope unless you want it in the registry now). |

## Standards research (issue step 1)

**Finding:** No single universal config covers *all* editor surfaces today.

| Surface | Portability |
|---------|-------------|
| `SKILL.md` skills | **Open standard** (Agent Skills / agentskills.io) — portable `name` + `description` + body. Cursor, Claude Code, Codex, VS Code Copilot, etc. consume it. |
| `AGENTS.md` | De-facto convergent always-on rules file; issue-flow already owns a managed `<!-- BEGIN/END issue-flow -->` block. |
| `.cursor/rules/*.mdc` | Cursor-specific (`alwaysApply`, `globs`, `paths`). |
| `CLAUDE.md` | Claude Code-specific layering on `AGENTS.md`. |
| Slash commands (`commands/`, `command/`) | Editor-specific paths and formats; shrinking as tools go skills-first. |
| `.issueflows/` | **Issue-flow canonical** — already editor-neutral issue tracking. |

**Conclusion:** Adopt **issue-flow canonical format** = committed `.issueflows/` + rendered skill snapshots under a neutral store + shared `AGENTS.md` block. Per-editor trees are **generated artifacts**, not the team source of truth.

## Approach

### Phase 1 (this PR) — canonical store + convert CLI

**1. Canonical layout (new)**

Introduce `.issueflows/agent/` as the team-committed store:

```text
.issueflows/
  agent/
    skills/<stem>/SKILL.md    # editor-neutral rendered skills (from templates)
    manifest.json             # issue-flow version, mode, skill_level, surfaces included
  config.toml                 # add canonical_format = true, optional team_editor hint
AGENTS.md                     # managed block (unchanged mechanism)
```

- Populated by `issue-flow init --canonical` or `issue-flow convert --to canonical`.
- Editor dirs (`.cursor/`, `.claude/`, `.opencode/`, `.codex/`) become **local-only** when `canonical_format = true` — document a `.gitignore` snippet (or `issue-flow convert --gitignore`) listing them.

**2. Refactor scaffold loop (issue step 3)**

Extract from `init.py`:

- `materialize_surfaces(project_root, profiles, *, mode, skill_level, force, target: Literal["editor","canonical"])`
- `init` / `update` call `target="editor"` (current behaviour).
- `convert` calls `target="editor"` for one profile or `target="canonical"` for the neutral store.

No second template tree — same `build_manifest()` + `_write_manifest_files()` paths, different output root mapping in one place.

**3. CLI (issue step 4)**

```bash
issue-flow convert --to cursor          # local dev: canonical → .cursor/ (+ docs, .mdc, AGENTS.md)
issue-flow convert --to claude
issue-flow convert --to canonical       # team: strip local editor dirs, refresh .issueflows/agent/
issue-flow convert --prune-other        # remove non-target editor trees after convert
```

Resolution order for target editor: `--to` flag > `ISSUEFLOW_EDITOR` / `.env` > `config.toml` `[issueflow].editor` (new persisted key, optional).

`convert` reuses active `mode` + `skill_level` from `config.toml` (same as `update`).

**4. Docs + design record**

- New `.issueflows/04-designs-and-guides/multi-editor-conversion.md` — canonical format, team vs solo workflows, gitignore guidance.
- Update `docs/configuration.md` — `canonical_format`, `convert`, editor persistence.
- README future-work cross-link.

**5. Tests**

- Unit: output path mapping canonical vs editor; `--prune-other` only removes known manifest paths.
- Integration: init canonical → convert to claude + cursor → assert skills present, no cross-editor leakage (reuse `test_templating` patterns).
- Extend `verify_scaffold.py` or parallel test for convert round-trip.

### Phase 2 (follow-up / can split to #101-adjacent issue) — git hooks (issue step 5)

```bash
issue-flow hooks install convert   # opt-in, shows script before writing
```

| Hook | Action |
|------|--------|
| `post-merge` / `post-checkout` | `issue-flow convert --to $ISSUEFLOW_EDITOR` (materialize local editor) |
| `pre-push` (default) or `pre-commit` (configurable) | `issue-flow convert --to canonical --prune-other` (ensure team format committed) |

- Scripts call installed `issue-flow` on PATH; fail loudly if missing.
- Document composing with #101's issue-file hooks (separate scripts, shared `core.hooksPath` or chained calls).
- **Open question:** pre-push vs pre-commit for canonicalization — see below.

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/init.py` | Extract `materialize_surfaces()`; optional canonical writer. |
| `src/issue_flow/convert.py` | **New** — convert orchestration, prune logic. |
| `src/issue_flow/cli.py` | `convert` subcommand; optional `init --canonical` flag. |
| `src/issue_flow/config.py` | `canonical_format`, persisted `editor` keys; template context for canonical paths. |
| `src/issue_flow/templating.py` | Canonical manifest helper (skills subset → `.issueflows/agent/skills/`). |
| `src/issue_flow/templates/config.toml.j2` | Document new keys (if template exists). |
| `docs/configuration.md` | User-facing config for conversion workflow. |
| `.issueflows/04-designs-and-guides/multi-editor-conversion.md` | **New** design doc. |
| `tests/test_convert.py` | **New** |
| `tests/test_init.py` / `tests/test_templating.py` | Adjust for extracted helper. |
| `.issueflows/00-tools/verify_scaffold.py` | Optional convert smoke. |

## Test strategy

```bash
uv run pytest tests/test_convert.py tests/test_init.py tests/test_templating.py tests/test_editors.py
uv run ruff check src/ tests/
```

Manual smoke: scaffold throwaway repo with `init --canonical`, `convert --to claude`, verify `.claude/skills/iflow-init/SKILL.md` exists and `.issueflows/agent/` unchanged.

## Open questions

1. **Phase boundary:** Implement Phase 1 only in this PR (recommended), or include git hooks now?
2. **Canonicalization hook timing:** Default `pre-push` (safer — avoids mid-commit surprise) or `pre-commit` (stricter — never commit local editor trees)?
3. **Solo back-compat:** Should `init` without flags keep writing `.cursor/` into git as today, or should we nudge new projects toward canonical + gitignored editor dirs in docs only?
4. **Windsurf (#17):** Defer until `EditorProfile` exists, or add stub profile in this work?

## Scope check

Full issue (#23) spans research + refactor + CLI + hooks — **too large for one focused PR**. This plan delivers the architectural refactor and conversion CLI (steps 1–4); hooks (step 5) are a clear Phase 2 with explicit overlap notes for #101.

If you want smaller still, Phase 1a could be refactor + `convert --to <editor>` only (no canonical store / gitignore), but that weakens the team story — canonical store is the point of the issue.
