# Issue #162 plan: Docs check (iPhone)

## Goal

Fix the published Zensical docs on iPhone: restore the header logo/favicon and make the CLI reference page reliably visible on mobile Safari.

## Constraints

- Docs-only change; no scaffold templates or CLI code.
- Keep nav structure and existing logo assets; do not reintroduce removed PNGs.
- Prefer minimal, targeted fixes over broad theme rewrites.

### Prior art

- [zensical.toml](zensical.toml) — `logo` points at missing `static/images/logo-pblue.svg` (commit `bf96830` changed path, file never added). Existing blue asset: `logo-light-right-color.svg`.
- [issue #151 plan](.issueflows/03-solved-issues/issue151_plan.md) — favicon deliberately skipped; issue #162 reports icon missing on phone.
- [docs/cli.md](docs/cli.md) — opens with a wide, unwrapped synopsis code block; `navigation.instant` + `navigation.instant.prefetch` enabled (known Safari SPA nav bugs).
- Toolbox — no doc-site helper.

## Approach

1. **Logo** — point `[project.theme] logo` at `static/images/logo-light-right-color.svg` (the committed blue gradient icon).
2. **Favicon** — set `favicon = "static/images/logo-black.svg"` so mobile tabs/bookmarks show the mark.
3. **Mobile CLI reliability** — drop `navigation.instant` and `navigation.instant.prefetch` from theme features (Safari/iPhone blank-page / dead-link reports with instant loading).
4. **Mobile overflow CSS** — add `docs/stylesheets/extra.css` via `extra_css`; enable horizontal scroll + touch momentum for wide `pre` blocks and tables.
5. **CLI synopsis** — add YAML frontmatter title; rewrap the opening command synopsis onto shorter lines so the block does not force horizontal overflow on narrow viewports.

## Files to touch

| File | Change |
| --- | --- |
| [zensical.toml](zensical.toml) | Fix logo path, add favicon, drop instant nav features, register `extra_css` |
| [docs/stylesheets/extra.css](docs/stylesheets/extra.css) | New — mobile overflow rules for code + tables |
| [docs/cli.md](docs/cli.md) | Frontmatter + wrapped synopsis block |

## Test strategy

- `uv run zensical build` — succeeds; built HTML references existing logo SVG and includes `extra.css`.
- `uv run pytest` — regression safety (no new tests; docs-only).

## Open questions

- None — scope is small and yolo-appropriate.
