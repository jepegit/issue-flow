# Issue #151 plan: add a logo

## Goal

Show the prototype logo (`docs/static/images/LOGO_01.png`) on the published
Zensical documentation site — header branding on every page, with the asset
committed so Read the Docs builds include it.

## Constraints

- Docs-only change; no scaffold templates or CLI code.
- Logo path must be relative to the Zensical `docs_dir` (default `docs/`).
- Keep existing `site_name`, nav, and theme palette unchanged unless duplication
  forces a tweak (see Open questions).
- Commit the image file; it is currently untracked.

### Prior art

- [zensical.toml](zensical.toml) — existing site config; `[project.theme]` has
  palettes and features but no `logo` yet. Zensical docs:
  [Logo and icons](https://zensical.org/docs/setup/logo-and-icons/) — set
  `[project.theme] logo = "<path-under-docs>"` for a PNG/SVG in `docs/`.
- [.readthedocs.yaml](.readthedocs.yaml) — RTD runs `zensical build`; no change
  needed if the logo lives under `docs/`.
- [docs/index.md](docs/index.md) — home page; no image branding today.
- Toolbox (`00-tools/`) — no doc-site helper; `verify_scaffold.py` is unrelated.
- Graph — no logo/docs-site nodes in `GRAPH_REPORT.md` (grep checked).

## Approach

1. **Wire the theme logo** — add to `[project.theme]` in `zensical.toml`:

   ```toml
   logo = "static/images/LOGO_01.png"
   ```

   Zensical copies files under `docs/` into the built site; `static/images/` is
   valid (same pattern as `images/logo.png` in upstream examples).

2. **Commit the asset** — stage `docs/static/images/LOGO_01.png` (already on
   disk from the issue author).

3. **Optional home-page prominence** — only if header alone feels too small:
   add a centered `![issue-flow](static/images/LOGO_01.png)` near the top of
   `docs/index.md`, above the `# issue-flow` heading. **Default: skip** — the
   issue asks to include the logo in Zensical docs; theme `logo` satisfies that
   without duplicating branding on the home page.

4. **Verify locally** — `uv sync --group docs` (if needed), then
   `uv run zensical build`; confirm `site/` contains the image and the built
   HTML references it in the header. Spot-check with `uv run zensical serve` if
   useful.

**Note on layout:** `LOGO_01.png` includes both the house/Git icon and
`issue-flow` wordmark. The theme also renders `site_name = "issue-flow"` beside
the logo — likely redundant. Prefer shipping theme logo first and adjusting only
if preview looks wrong (see Open questions).

## Files to touch

| File | Change |
| --- | --- |
| [zensical.toml](zensical.toml) | Add `logo = "static/images/LOGO_01.png"` under `[project.theme]` |
| [docs/static/images/LOGO_01.png](docs/static/images/LOGO_01.png) | Add to git (no edit) |
| [docs/index.md](docs/index.md) | *Optional* — hero image if user wants extra prominence |

## Test strategy

- `uv run zensical build` — must succeed; inspect `site/` for
  `static/images/LOGO_01.png` (or equivalent copied path) and logo in header HTML.
- `uv run pytest` — run at `/iflow-close` for regression safety (no new tests
  expected; docs change only).
- `uv run ruff check src/ tests/` — unchanged expectation (clean).

## Open questions

1. **Header duplication** — logo PNG already says "issue-flow" while
   `site_name` does too. Options: (a) ship as-is and tweak after visual review,
   (b) hide/shorten `site_name` if Zensical allows without looking broken, (c)
   swap to an icon-only crop later. **Recommendation: (a)** for this prototype
   issue.
2. **Favicon** — also set `favicon = "static/images/LOGO_01.png"`? Wordmark may
   be illegible at 16×16. **Recommendation: skip favicon** unless you want to
   try it.
3. **Filename** — keep `LOGO_01.png` or rename to `logo.png`? **Recommendation:
   keep as-is** — matches issue wording and avoids churn.
