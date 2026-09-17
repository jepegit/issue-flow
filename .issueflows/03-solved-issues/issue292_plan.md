# Plan: #292 Confirm or skip opencode's user-global skill path

## Goal

Table row is `verified` (or `skip`). Stage 3 materialize never guesses.

## Approach

Official docs (2026-09-17):
https://opencode.ai/docs/skills/ — global write target is
`~/.config/opencode/skills/<name>/SKILL.md`. Compat also reads
`~/.claude/skills/` and `~/.agents/skills/`. Record **verified**; do
not write compat paths as primary. No `src/` install.

## Files to touch

- `.issueflows/04-designs-and-guides/global-vs-local-skills.md`
- `epic269_plan.md` (Published lines from Stage 3)

## Test strategy

Doc-only. Acceptance is the table row.
