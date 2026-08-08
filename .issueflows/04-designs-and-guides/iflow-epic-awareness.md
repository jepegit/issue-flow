# `/iflow` epic awareness

**Issue:** [#210 — Iflow in epics](https://github.com/jepegit/issue-flow/issues/210)
**Related:** [#139](https://github.com/jepegit/issue-flow/issues/139) (`/iflow-pick` epic preference + stage gates)

## Context

`/iflow-pick` already surfaces an active epic’s current-stage
`next_candidates` via `issue-flow agent epic-status`. Plain `/iflow` /
slash-less `iflow` did not: with no focus issue it fell through to
`/iflow-init` and asked for a number, which feels broken mid-epic.

## Decision

When `/iflow` has **no resolvable focus** (no `^\d+-.+` branch, empty
`01-current-issues/`):

1. Read `epic_hint` from `issue-flow agent state --json` (or scan
   `05-epics/` + `epic-status` as fallback).
2. If any `next_candidates` → **stop**, list them, recommend `/iflow-pick`.
   Never auto-dispatch pick; never silent-pick even for one candidate.
   Trailing explicit `N` may still dispatch `/iflow-init <N>`.
3. If none → today’s state A → `/iflow-init`.

With a resolved focus, A/B/C/D dispatch is unchanged. Soft report hint
after close when an epic still has candidates is optional.

## CLI

`agent state --json` includes `epic_hint: { epics: [...] }` only when
there is no focus (and focus is not ambiguous). Each entry:
`epic`, `title`, `stage`, `stage_title`, `next_candidates`.

## Non-goals

- Auto-dispatch to `/iflow-pick` / `/iflow-cycle` / `/iflow-auto`
- Changing epic publish or stage-gate offers (#139)
