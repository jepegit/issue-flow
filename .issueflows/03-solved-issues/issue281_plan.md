# Plan: #281 Design doc — user-global config

## Goal

One merged design doc answers path, precedence, lock, registry, and
`update --all` vs `workspace update`. Knobs table gains the new rows.
Stage 2 specs in `epic269_plan.md` cite the doc.

## Approach

Write `.issueflows/04-designs-and-guides/user-global-config.md` with
decided policy (not options). Pick **project > user-global > env >
default** so it extends the existing knobs contract instead of reversing
it. Lock stays a **project** key. Registry + `update --all` live under
the XDG (or Windows APPDATA) user dir and do not require
`issueflow-workspace.toml`. Honour #276 stamps per registered repo;
`--force` on `--all` forwards.

Add knobs-table rows and a short pointer in `docs/configuration.md`.
Cite the doc from unpublished Stage 2 issue specs.

No `src/` behaviour in this issue.

## Files to touch

- `.issueflows/04-designs-and-guides/user-global-config.md` (new)
- `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`
- `.issueflows/05-epics/epic269_plan.md`
- `docs/configuration.md`

## Test strategy

Doc-only. Existing `uv run pytest` must stay green. No new tests.
