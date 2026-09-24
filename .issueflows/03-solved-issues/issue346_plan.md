# Plan — Issue #346: docs: regroup navigation and the How-to index

(Epic #341 stage 2, via /iflow-drive → /iflow-auto → /iflow-cycle; yolo chain, auto-confirmed. Planned as yolo: no; the scope is small, nav config plus one index page.)

## Goal

The nav is grouped Getting started / How-to (Everyday, Faster, Bigger changes, Team and repos) / Reference / For agents / Project. No file under `docs/` is renamed, and the link check passes.

## Approach

- `zensical.toml` nav: move Choose a mode and Editor support under Getting started. Group the how-tos. Reference = Commands / CLI / Configuration / Graphify. For agents gets its own entry. Project = Developing / Changelog / Acknowledgements.
- Concepts: leave a comment in the nav; #347 adds the page. Deliberately no empty stub page on the live site.
- pstack skills didn't fit the four named groups, so it gets a small **Extras** group.
- Enable `navigation.tabs` (6 tabs, so each sidebar only shows its own section).
- Rewrite `docs/how-to/index.md` as grouped tables matching the nav, plus an "Elsewhere" pointer for the moved pages.

## Test strategy

Build with zensical, inspect the tabs and sidebar in the HTML, run `scripts/check_doc_links.sh`, run `uv run pytest`.
