# Issue #117 plan: great skills

Source issue: [issue117_original.md](issue117_original.md)

## Goal

Vendor mattpocock's [writing-great-skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-great-skills) skill into this repo as a reference, then audit and update the skill templates issue-flow ships so they follow its best practices.

## Constraints

- **Templates are the source of truth** — edit `src/issue_flow/templates/skills/*/SKILL.md.j2`, never the rendered copies under `.cursor/skills/`; re-render via `issue-flow update` afterwards (per `AGENTS.md` and `this-project.md`).
- **Behavior-preserving** — pruning/conformance only. All workflow semantics (confirmations, off-path markers, `- [x] Done` rules, file-movement rules, output contracts) must survive in meaning. No lifecycle changes.
- Upstream repo is **MIT-licensed** — vendor with attribution header (source URL + license note).
- Jinja2 variables (`{{ issueflows_dir }}` etc.) and the `_model_directive.md.j2` include must keep rendering; verify with the scaffold checker.

### Prior art

- `.issueflows/00-tools/verify_scaffold.py` — end-to-end scaffold render check; reuse it, don't write a new checker.
- `.issueflows/04-designs-and-guides/caveman-skill.md`, `grill-me-skill.md` — existing pattern of per-skill design docs; a new `skill-authoring.md` guide follows the same convention.
- `src/issue_flow/templates/skills/_model_directive.md.j2` — shared include; conformance edits must keep it.

## Approach

1. **Vendor the reference** into `.cursor/skills/writing-great-skills/` (`SKILL.md` + `GLOSSARY.md`, faithful copies with a short attribution header: source URL, fetch date, MIT). User-invoked (`disable-model-invocation: true`) — zero context load; it is a reference we reach for when editing skill templates. This folder is not touched by `issue-flow update` (only its own managed skills are rewritten).
2. **Add a terse authoring guide** `.issueflows/04-designs-and-guides/skill-authoring.md`: the decision (we follow the vendored reference), house rules distilled for issue-flow templates (user-invoked skills get one-line human-facing descriptions; model-invoked skills — caveman, grill-me — keep trigger-rich descriptions; shared material goes behind pointers like `iflow-comments`; no-op/sediment pruning discipline), link back to issue #117.
3. **Audit all 18 skill templates** against the reference and fix conformance issues. Known findings to fix:
   - **Descriptions on user-invoked skills** — every `iflow-*` skill sets `disable-model-invocation: true` yet carries a multi-line trigger-rich description. Per the reference, a user-invoked description is a one-line human-facing summary; trim all of them.
   - **"When to use" trigger lists in user-invoked skills** — partly no-op (only the human invokes); keep genuinely behavior-bearing lines (e.g. "do not use from /iflow"), drop trigger phrasing.
   - **Duplication** — `iflow_init` inlines a "Summary of rules" copy of `iflow_comments`' triage rules; collapse to the context pointer. Hunt equivalents elsewhere.
   - **No-ops / sediment** — sentence-level pass over each template ("Use UTF-8 for markdown output", restated defaults, stale lines).
   - **Completion criteria** — sharpen vague step ends where cheap and safe.
4. **Re-render this repo's own scaffold** (`issue-flow update` dogfood) so `.cursor/skills/` and `.cursor/commands/` match the new templates.
5. **Note, don't fix**: `templates/commands/*.md.j2` duplicate skill content wholesale (~1070 lines) — a single-source-of-truth violation, but restructuring the command/skill split is its own issue (see Open questions).

Order: 1 → 2 → 3 (worst offenders first: `iflow_comments`, `iflow_history_update`, `iflow_init`) → 4 → tests.

## Files to touch

- `.cursor/skills/writing-great-skills/SKILL.md`, `GLOSSARY.md` — new, vendored with attribution.
- `.issueflows/04-designs-and-guides/skill-authoring.md` — new, terse house rules + pointer.
- `src/issue_flow/templates/skills/*/SKILL.md.j2` — 18 files, conformance edits (descriptions, trigger-list pruning, duplication collapse, no-op removal).
- `.cursor/skills/*/SKILL.md`, `.cursor/commands/*` — re-rendered by `issue-flow update` (mechanical).
- `tests/` — update any assertions pinned to old description text (check first).

## Test strategy

- `uv run pytest` — full suite.
- `uv run ruff check src/ tests/` — lint.
- `uv run .issueflows/00-tools/verify_scaffold.py` — end-to-end scaffold render + marker checks (label-driven yolo routing, hands-off close markers must survive).
- Grep rendered output for load-bearing markers (`disable-model-invocation`, off-path notes, `- [x] Done`) after re-render.

## Open questions

1. **Command/skill duplication** — recommend filing a follow-up issue ("commands should be thin pointers to skills, or generated from them") instead of folding it into this PR. Confirm?
2. **Vendored copy location** — recommend `.cursor/skills/writing-great-skills/` (agent-reachable while editing templates) over a plain doc in `04-designs-and-guides/`. Confirm?
3. **Scaffold the reference into target projects too?** Issue says "our issue-flow repository", so recommend **no** — repo-local only, not a new template. Confirm?
4. **Audit depth** — recommend full behavior-preserving pruning pass per skill (not just descriptions). Confirm?
