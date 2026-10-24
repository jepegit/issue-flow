# Issue #410: Positive-phrasing pass over the lifecycle mode files (follow-up to #268)

Source: https://github.com/jepegit/issue-flow/issues/410

## Original issue text

## Problem / context

#268 adopted the *Negation* rule from `writing-for-agents`: a "do not X" primes X, so state the positive target, and keep "never" only as a hard guardrail paired with that target. #268 applied it to the 13 router `SKILL.md` files, caveman, grill-me and the shared partials (102 → 32 prohibitions). The 26 mode files were deferred to keep that diff reviewable. They still carry **195** `do not / don't / never / must not` phrases. The heaviest are `iflow-issue/epic.md` (20), `iflow-run/cycle.md` (16), `iflow-close/changelog.md` (14), `iflow-run/drive.md` (13), `iflow-run/auto.md` and `iflow-close/version.md` (12 each).

## Spec

- For every hit in `src/issue_flow/templates/skills/iflow_*/<mode>.md.j2`, do one of three things:
  - Convert it to the positive target.
  - Remove it as a duplicate of the router or Constraints.
  - Keep it as a guardrail next to its positive target (destructive git, skipped confirms, silent picks, merge or force-push scope).
- Follow the house rules in `skills-and-styles.md#skill-authoring`, and keep behavior identical: confirmations, off-path markers, `- [x] Done` rules, file moves, output contracts.
- Update tests that pin old prohibition strings to pin the positive wording.
- Re-render with `issue-flow update`.

## Acceptance criteria

- Every one of the 195 hits is accounted for in the issue's status file as converted, removed, or kept-as-guardrail.
- `uv run pytest`, `uv run ruff check src/ tests/` and `issue-flow doctor` (no `skill_spec_*` errors) are clean.
- Mode-file word counts don't grow, and the `test_command_surface.py` budgets still pass.

## Out of scope

Flattening mode-to-mode delegation (`drive` → `epic` → `auto` → `cycle` → `yolo`).
