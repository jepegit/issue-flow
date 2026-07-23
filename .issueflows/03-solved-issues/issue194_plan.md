# Plan — #194 `/iflow-auto` orchestrator skill (skeleton)

## Goal

Ship an off-path `/iflow-auto` skill+command skeleton that composes `/iflow-cycle`
over a confirmed epic stage, records `auto_status.md`, and stubs the adversarial
gate for Stage 2.

## Constraints

- No real adversarial reopen/create in this issue.
- Off-path only; never auto-dispatched by `/iflow`.
- Compose existing cycle/yolo/epic surfaces; do not fork them.
- Contract names from `advanced-auto-mode.md`.

## Approach

1. Add `iflow_auto` / `iflow-auto` templates; register in `templating.py` +
   `step_profiles.toml` (`reasoning`).
2. Document off-path in rules, dispatcher, workflow doc, README, docs index.
3. Behaviour: confirmed epic → select stage → overnight confirm →
   `auto_status.md` → `/iflow-cycle` → adversarial stub → stop.
4. Support `status` / `dry-run` / `loops:<n>` / optional `stage <k>`.
5. Tests: registration, render, manifest counts, off-path listing.

## Files to touch

- `src/issue_flow/templates/skills/iflow_auto/SKILL.md.j2` (new)
- `src/issue_flow/templates/commands/iflow-auto.md.j2` (new)
- `src/issue_flow/templating.py`, `step_profiles.toml`
- Docs/rules/dispatcher templates + README + `docs/index.md`
- `tests/test_templating.py`, `HISTORY.md`

## Test strategy

`uv run pytest` + `uv run ruff check src/ tests/`.

## Open questions

None — follows confirmed epic #169 Stage 1 + design doc #191.
