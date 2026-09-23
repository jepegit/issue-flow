# Status: #339 no iflow init in agents

- [x] Done

## What's done

- Plan accepted (2026-09-23).
- `materialize_user_global_both_skills` writes `both` stems to every editor user-global path (`EDITORS.values()`). `--editor` still selects only the project tree.
- Tests: Cursor-only init now asserts `~/.agents/skills` and `~/.claude/skills` get `iflow-init` (and the other mode-allowed `both` stems).
- Docs: `global-vs-local-skills.md`, `docs/configuration.md`, `docs/how-to/for-agents.md`, `test-registry.md`.
- `uv run pytest` — 854 passed. `ruff check --fix` clean.
- Close: bumped `0.5.9` → `0.5.10`; HISTORY promoted with #318 + #339.

## Remaining work

None.
