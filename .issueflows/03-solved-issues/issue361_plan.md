# Plan — Issue #361: docs: add diagrams for the lifecycle, folder moves and epic flow

(Epic #341 stage 4, via /iflow-drive run 2 → auto → cycle; yolo chain, auto-confirmed. Planned as yolo: no because of the rendering decision. Zensical documents a Mermaid fence, which made the decision straightforward.)

## Goal

Three diagrams render in light and dark mode on the site, and the rendering decision is recorded.

## Approach

- `zensical.toml`: add the Mermaid `custom_fences` entry to `pymdownx.superfences` (the form Zensical's own bootstrap config uses).
- `docs/concepts.md`: replace the lifecycle and folder-move text sketches with Mermaid flowcharts, and add a dispatcher decision chart (off-path commands dotted) above the existing table.
- `docs/how-to/epics.md`: add an epic-flow flowchart above the existing text tree.
- Design note `04-designs-and-guides/docs-diagrams.md`: Mermaid vs SVG vs ASCII, conventions, caveats (no Mermaid in scaffolded templates).

## Test strategy

Build; headless Chromium (Playwright) screenshots of every diagram in both palette schemes; link check; pytest.
