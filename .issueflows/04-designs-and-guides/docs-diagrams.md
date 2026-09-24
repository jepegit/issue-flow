# Diagrams in the docs

**Issue:** [#361](https://github.com/jepegit/issue-flow/issues/361) (epic #341).
**Status:** decided 2026-09-24.

## Context

The workflow is visual (a lifecycle, folder moves, staged epics), but the docs
site had only plain-text sketches. We needed a way to add diagrams that
survive edits and work in light and dark mode.

## Decision

Use **Mermaid** through Zensical's `pymdownx.superfences` custom fence
(configured in `zensical.toml`). Write diagrams as ` ```mermaid ` blocks in
the markdown. The theme loads Mermaid in the browser and restyles diagrams
when the reader switches between light and dark mode.

Current diagrams:

- `docs/concepts.md`: the lifecycle (pick → cleanup), what `iflow` dispatches from which file state (with off-path commands dotted), and folder moves between `01-` / `02-` / `03-`.
- `docs/how-to/epics.md`: the epic flow (anchor → plan → publish → stages). The old text tree stays underneath.

Conventions:

- Use `flowchart` with short labels. `<br/>` for line breaks.
- Solid arrows for what issue-flow does on its own; dotted (`-.->`) for off-path commands the user runs.
- No custom colours, so the theme's palette applies in both modes.

## Alternatives considered

- **SVGs committed under `docs/static/images/`.** They look the same everywhere, but need an external editor, are hard to review in diffs, and don't adapt to dark mode without two copies.
- **ASCII art only.** Works in any markdown viewer (and stays in the scaffolded `docs/issue-workflow.md`, which is read inside projects), but is hard to read on the site.

## Caveats

- Mermaid renders client-side (loaded from a CDN by the theme). Readers without JavaScript see the Mermaid source, which is still readable.
- Diagrams are **not** used in scaffolded templates such as `issue-workflow.md.j2`. Editors and GitHub may not render them, so those keep text sketches.

## Verification

Checked with headless Chromium (Playwright) in both palette schemes: every diagram renders to SVG, with readable text on the dark background.
