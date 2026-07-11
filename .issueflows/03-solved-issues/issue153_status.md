# Issue #153 status: possible misplacement of mode information

- [x] Done

## Summary

The `## Scaffolding modes` block in `docs/developing.md` duplicated user-facing
content already covered in `docs/configuration.md` (added intentionally in #48,
redundant after configuration.md matured). Replaced it with a contributor-focused
`## Working on scaffolding modes` section that links to configuration.md and
keeps package-maintainer pointers (modes.toml, modes.py, template membership
gating, smoke test, tests).

## What landed

- [docs/developing.md](../../docs/developing.md) — trimmed ~35 lines of duplicate
  user docs; added slim contributor section
- `uv run zensical build` — clean
- No configuration.md cross-link (kept user doc pure)

## Tests

- `uv run pytest` — 456 passed
- `uv run ruff check src/ tests/ scripts/` — clean
