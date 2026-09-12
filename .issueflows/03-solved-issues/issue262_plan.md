# Plan — Issue #262: task-oriented how-to guides

## Goal

Add a **How-to** section on the Zensical docs site with short procedural pages (goal → steps → related links), including epics and auto, and point Getting started / Home at them.

## Constraints

- How-tos stay procedural; do not duplicate full `issue-workflow.md`.
- Prefer linking public docs + existing design docs over copying them.
- At least **6** pages; ship the full first set from the issue (≥8 topics + index).
- ### Prior art
  - Nav: flat `nav = [...]` in `zensical.toml` (nested section for How-to).
  - Tone/structure: `docs/getting-started.md`, Recipes on `docs/index.md`.
  - Modes table: `docs/configuration.md#modes`; design: `.issueflows/04-designs-and-guides/modes.md`, `advanced-auto-mode.md`, `pr-queue-sync.md`.

## Approach

1. Create `docs/how-to/` with `index.md` plus one page per topic.
2. Wire a nested **How-to** section into `zensical.toml` nav (after Getting started).
3. Add “Where to go next” / Recipes links from `getting-started.md` and `index.md`.
4. Verify with `uv run zensical build`.

## Files to touch

| Path | Change |
|------|--------|
| `docs/how-to/index.md` | How-to index |
| `docs/how-to/*.md` | 8 task pages |
| `zensical.toml` | Nested How-to nav |
| `docs/getting-started.md` | Link how-to index |
| `docs/index.md` | Point Recipes at how-tos |

## Test strategy

- `uv run zensical build` (docs must build)
- `uv run pytest` (no code change expected; yolo gate)

## Open questions

- None — yolo auto-confirm.
