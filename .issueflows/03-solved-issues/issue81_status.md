# Issue #81 status: add caveman skill

- [x] Done

## What's done

- Added the caveman skill template
  `src/issue_flow/templates/skills/caveman/SKILL.md.j2` (full intensity only,
  English only, model-invocable frontmatter; off via "stop caveman" / "normal
  mode").
- Registered `caveman` in `SKILL_DIRS` (`src/issue_flow/templating.py`) so the
  `standard` mode installs it and `simple` omits it. Existing
  `_prune_excluded_surfaces` removes it on a `standard -> simple` switch.
- Added a membership-gated pointer to `src/issue_flow/templates/rules/_body.md.j2`
  (shows in `AGENTS.md` / `CLAUDE.md` / `.mdc` only when caveman is installed).
- Docs: README "Modes" note + design note
  `.issueflows/04-designs-and-guides/caveman-skill.md`.
- Tests: updated manifest counts (17->18 cursor, 16->17 codex) and added caveman
  coverage in `tests/test_templating.py` and `tests/test_modes.py`.

## Verification

- `uv run pytest` -> 193 passed.
- `uv run ruff check src/ tests/` -> clean.
- Smoke: `init` (standard) writes `.cursor/skills/caveman/SKILL.md` + the AGENTS
  pointer; `init --mode simple` prunes both.

## Remaining

- None. Ready for `/iflow-close` (tests, version bump, HISTORY, commit, PR).
