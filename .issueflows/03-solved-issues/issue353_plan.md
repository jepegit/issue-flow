# Plan — Issue #353: docs: fix dead external links found by the docs link check

(Inter-epoch blocker from the epic #341 Stage 1 adversarial review. Re-queued via /iflow-auto loop 1; yolo chain, auto-confirmed.)

## Goal

The external step of the docs link check reports 0 errors, and `iflow-graphify.net` no longer appears anywhere.

## Approach

- `iflow-graphify.net` → `graphify.net` in 4 templates plus `README.md` and `docs/graphify.md`. Re-render so `AGENTS.md`, `.cursor/` and `docs/issue-workflow.md` pick it up.
- graphify LICENSE → `/blob/v8/LICENSE` (the default branch is `v8`).
- lychee install URL → `/guides/getting-started/`. PEP 440 URL → `/specifications/version-specifiers/`.
- New essential test rejects `iflow-graphify.net`. Add a registry row.

## Test strategy

Run lychee locally in external mode on the staged site. `uv run pytest`.
