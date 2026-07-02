# Issue #108 — plan

## Goal

README lacks attribution for the `grill-me` Agent Skill. Add a reference to its
source repo/author, matching the existing `caveman` attribution pattern.

## Approach

- The skill was adapted from Matt Pocock's `grill-me` skill (issue #32,
  `.issueflows/04-designs-and-guides/grill-me-skill.md`).
- Source repo: https://github.com/mattpocock/skills (MIT licensed, `LICENSE` in
  repo root).
- Add a row to the acknowledgements table in `README.md` (the table that already
  credits `JuliusBrussee/caveman`), describing it as the inspiration for the
  bundled `grill-me` skill, adapted to issue-flow's planning workflow.

## Files to touch

- `README.md` (one table row)

## Test strategy

- `uv run pytest` (full suite; docs-only change, tests guard against regressions)
- Visual check of the table markdown.
