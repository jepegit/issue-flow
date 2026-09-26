# Status — Issue #388: more knobs for automatically accepting and for continuing

- [x] Done

## What's done

- Plan accepted: `cleanup_yes_a1`, `cleanup_yes_a2`, `auto_cleanup` (all default false). Watch-only, no auto-merge.
- Knobs plumbed (`modes` / `config` / `config_ops`) and baked into cleanup, close, yolo, and cycle templates.
- `issue-flow update` warns when `cleanup_yes_a2` is on.
- Design inventory in `skill-behaviour-knobs.md`. Docs settings table updated.
- This repo's `config.toml` left off.
- Essential review: new tests left unmarked (config bake and the A2 warning). The settings-table test was already essential and covers the new keys.
- Version bump `0.5.14` → `0.5.15` (patch; command was `bump`). No publish label.
- `HISTORY.md` promoted to `0.5.15` (2026-09-26). Essential tests: 24 passed. Ruff clean.

## Remaining work

- None. PR, then `/iflow-cleanup` after merge.
