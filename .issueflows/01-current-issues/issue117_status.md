# Issue #117 status: great skills

- [x] Done

## What's done

- Vendored mattpocock's `writing-great-skills` reference (SKILL.md + GLOSSARY.md, MIT, upstream commit `d11147d`) into `.cursor/skills/writing-great-skills/` with an attribution header.
- Added `.issueflows/04-designs-and-guides/skill-authoring.md` — the decision to follow the reference plus house rules distilled for issue-flow templates.
- Audited all 18 skill templates under `src/issue_flow/templates/skills/` against the reference and applied behavior-preserving conformance edits:
  - Trimmed every user-invoked (`disable-model-invocation: true`) skill's description to a one-line human-facing summary (trigger lists belong only to model-invoked skills).
  - Removed "When to use" trigger sections from user-invoked skills, keeping behavior-bearing lines (off-path / do-not-use-from rules) in the intro; only model-invoked `grill-me` keeps its trigger section.
  - Collapsed duplication: `iflow_init`'s inline copy of the `iflow_comments` triage rules is now a pointer; `iflow_close`'s restated version-bump level table defers to `iflow-version-bump`; caveman's Intensity section no longer repeats its Rules; `iflow_history_update`'s `nohistory` rule now lives in one place.
  - Pruned no-ops/sediment ("Use UTF-8", stale `--bump <patch|minor|major>` level list in close).
  - Fixed a structural defect: `iflow_pick` was missing its `### Phase 2 — create the branch` heading.
- Re-rendered this repo's own scaffold via `issue-flow update` (18 skills + rule + doc).

## Testing

- `uv run pytest` — 331 passed.
- `uv run ruff check src/ tests/` — clean.
- `uv run .issueflows/00-tools/verify_scaffold.py` — all checks passed (label routing, hands-off close markers, config flips).
- Fresh end-to-end scaffold into a throwaway project confirmed the new descriptions render and only `grill-me` keeps a "When to use" section.

## Remaining work

- None for this issue. Follow-up candidate (not filed): `templates/commands/*.md.j2` duplicate skill content wholesale (~1070 lines) — single-source-of-truth violation, tracked in `skill-authoring.md` under "Known debt".
