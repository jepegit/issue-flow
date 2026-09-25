# Status — #382 bleeding edge

- [x] Done

## What's done

- Knob `on_bleeding_edge` (default false) wired through modes / config / config_ops / render.
- `issue-flow agent self-update`: `uv tool install issue-flow@latest` then subprocess `issue-flow update --skip-dep-check`. Skips editable/path installs.
- `/iflow-cleanup` skill + command: tokens `bleeding edge` / `no bleeding`; Phase A1 after successful FF pull on home. Workspace walk upgrades once.
- Docs: configuration, cli, for-agents, issue-workflow, skill-behaviour-knobs.
- Tests: `tests/test_self_update.py` plus knob coverage. Essential suite 18 passed; full suite 906 passed at build.
- Essential review: new `test_self_update.py` left unmarked (mocked); registry updated.

## Remaining work

- None.
