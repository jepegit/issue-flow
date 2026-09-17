# Plan: #282 Skill split — global vs local

## Goal

Every default packaged stem classified `global` | `local` | `both`.
Cursor and Claude user-global paths verified (or marked unknown with
a Later follow-up). No `src/` install.

## Approach

Write `.issueflows/04-designs-and-guides/global-vs-local-skills.md`
with the stem table, editor-path table (cite Cursor docs), and
local-wins rule. Cross-link from `user-global-config.md`.

Placement: lifecycle `iflow_*` stay **local** (tied to this repo's
mode / `.issueflows/` / packaged version). Behaviour stems
`caveman`, `grill_me`, `gh_ci` are **both** (user-style, still
written in-project so a clone is self-contained). pstack stems stay
**local** (opt-in via `pstack_skills`).

## Files to touch

- `.issueflows/04-designs-and-guides/global-vs-local-skills.md` (new)
- `.issueflows/04-designs-and-guides/user-global-config.md` (pointer)
- `.issueflows/05-epics/epic269_plan.md` (Later cites the table)

## Test strategy

Doc-only. `uv run pytest` stays green.
