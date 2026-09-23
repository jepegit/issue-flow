# Plan: #339 — no iflow init in agents

## Goal

A default `issue-flow update` / `init` (Cursor-only `--editor`) also plants
user-global `iflow-init` where other harnesses look, especially Codex /
`.agents/skills`. Switching harness must not require a second `--editor`
pass just to get the chicken-egg skill.

## Constraints

- Do **not** collapse editors into one shared tree. Cursor Cloud still
  syncs only `~/.cursor/skills/`; Claude stays `~/.claude/skills`; Codex
  stays `~/.agents/skills`; opencode stays XDG `opencode/skills`.
  ([global-vs-local-skills.md](../04-designs-and-guides/global-vs-local-skills.md))
- `--editor` still controls **project-local** files only
  (`.cursor/` vs `.claude/` vs `.codex/`).
- Foreign user-global dirs still skip unless `--force`.
- Mode still gates which `both` stems exist (`simple` has no caveman).
- Do not add a fifth project `agent_dir` of `.agents/` — that is not a
  profile. Codex project skills stay `.codex/skills/`.
- House rules: [editor-profiles.md](../04-designs-and-guides/editor-profiles.md),
  [skill-authoring.md](../04-designs-and-guides/skill-authoring.md).

### Prior art

- `materialize_user_global_both_skills` (`surfaces.py`) — loops **selected
  `profiles` only**. Default update → Cursor → `~/.cursor/skills/` only.
- `editor_user_global_skills_root("codex")` → `~/.agents/skills` — the
  folder in the issue listing.
- `BOTH_SKILL_STEMS` = `caveman`, `grill_me`, `gh_ci`, `iflow_init`
  (`templating.py`). `#310` made `iflow_init` `both`; write target was
  still “selected editor.”
- `tests/test_global_both_skills.py` **locks the bug in**: Cursor init
  asserts Claude/Codex globals are absent.
- Docs: `docs/configuration.md` and `docs/how-to/for-agents.md` say
  user-global `iflow-init` is written on first `init`/`update`, but
  “selected editor” is the actual rule.
- Toolbox: `verify_scaffold.py` — optional after the fan-out; no new
  `00-tools/` script.
- Graph: skipped (editor / user-global paths already known).

## Approach

Fan-out user-global `both` stems to **every** registered editor path on
each `init` / `update`, regardless of `--editor`.

1. In `materialize_user_global_both_skills`, iterate
   `resolve_editors(["all"])` (or `EDITORS.values()`) for the **global**
   write loop. Keep using the caller’s `profiles` only for project
   materialize (unchanged).
2. Template context for each global write still uses that editor’s
   `EditorProfile` so stamps stay `cursor/iflow-init`, `codex/iflow-init`,
   …
3. Flip the tests that assert “Cursor init does not touch Claude/Codex
   globals.” New contract: Cursor-only `run_init` writes
   `iflow-init` (and the other mode-allowed `both` stems) under
   `~/.agents/skills`, `~/.claude/skills`, `~/.cursor/skills`, and
   opencode XDG. Project tree is still Cursor-only.
4. Docs: `global-vs-local-skills.md` (Materialize),
   `docs/configuration.md` (also fix the “three both skills” line —
   `iflow-init` is the fourth), `docs/how-to/for-agents.md` (one
   `update` plants globals for all harnesses).

`--editor` is not a global-install filter. Someone who wants only Cursor
globals is out of scope (say **Revise** if you want a later opt-out).

## Files to touch

- `src/issue_flow/surfaces.py` — fan-out loop.
- `tests/test_global_both_skills.py` — invert isolation asserts; add
  Cursor-init → `~/.agents/skills/iflow-init` exists.
- `.issueflows/04-designs-and-guides/global-vs-local-skills.md`
- `docs/configuration.md`
- `docs/how-to/for-agents.md`
- `.issueflows/04-designs-and-guides/test-registry.md` — row if we mark
  the new assertion essential.

## Test strategy

- `uv run pytest tests/test_global_both_skills.py tests/test_init.py tests/test_update.py -q --tb=line`
- `uv run ruff check src/ tests/`
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py`

## Open questions

None that block. Fan-out is **all** `both` stems (not only `iflow-init`)
so a harness switch also gets caveman / grill-me / gh-ci. **Revise** if
you want init-only.
