# Issue #151 status: add a logo

- [x] Done

## What's done

- Added `logo = "static/images/LOGO_01.png"` to `[project.theme]` in `zensical.toml`
- Committed prototype asset at `docs/static/images/LOGO_01.png`
- `uv run zensical build` succeeds; built site has `site/static/images/LOGO_01.png` and header `<img>` on all pages
- Skipped optional home-page hero, favicon, and rename per plan recommendations
- `uv run pytest` — 456 passed; `uv run ruff check src/ tests/` — clean

## Remaining work

- None
