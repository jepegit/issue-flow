# Issue #121 status: skill version stamp

- [x] Done

## What's done

- Added `issue_flow_version` to Jinja render context (from package `__version__`).
- `stamp_skill_version()` injects/refreshes `issue-flow-version: <ver>` in each rendered skill's YAML frontmatter.
- `render_template()` applies stamp for all `skills/*/SKILL.md.j2` outputs (includes caveman/grill-me).
- Workflow doc notes how to compare `issue-flow --version` with skill frontmatter.
- Re-rendered scaffold via `issue-flow update`.

## Testing

- `uv run pytest` — 345 passed.
- `uv run ruff check src/ tests/` — clean.

## Remaining work

- None.
