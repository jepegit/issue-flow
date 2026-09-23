# Status: #337 noob Recommended should follow epic session

- [x] Done

## What's done

- Plan accepted (2026-09-23).
- Rewrote `_noob_next.md.j2`: decision table (focus → `next_command`; session + candidates → `/iflow`; no session + candidates → `/iflow-pick`; session + empty hint → `epic-status` then publish or status; else capture). Epic stem list includes `/iflow-epic <N> publish`.
- Templating test `test_noob_footer_epic_gap_uses_session_not_next_command`.
- Docs: `docs/configuration.md`, `skill-behaviour-knobs.md`, `epic-start.md`, `test-registry.md`.
- `issue-flow update` in this worktree (noob is off here, so rendered skills have no footer — template is the ship vehicle).
- `uv run pytest tests/test_templating.py tests/test_cli.py` — 265 passed. `ruff check src/ tests/` clean.

## Remaining work

None. Ready for `/iflow-close`.
