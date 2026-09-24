# Issue #361: docs: add diagrams for the lifecycle, folder moves and epic flow

Source: https://github.com/jepegit/issue-flow/issues/361

## Original issue text

## Context and spec

Final-review finding for epic #341 (acceptance criterion "diagrams"; review §9). The Concepts page (#347) uses plain-text sketches. Add real diagrams:

1. **Lifecycle state machine:** what `iflow` dispatches to from which file state, plus where the off-path commands attach.
2. **Folder moves:** issue groups moving `01-current` → `02-partly-solved` / `03-solved` (close, pause, sweep).
3. **Epic flow:** anchor issue → plan → stages → published issues → cycle / auto / drive.

First decide on the rendering: Mermaid through a `pymdownx.superfences` custom fence (check Zensical support and dark-mode legibility), or SVGs committed under `docs/static/images/`. Record the decision in `.issueflows/04-designs-and-guides/`. Place the diagrams in Concepts (1, 2) and `how-to/epics.md` (3).

**Goal:** three diagrams render on the live site in light and dark mode, and the rendering decision is recorded.

**Model:** deep

Depends on: #348

Part of epic #341.
