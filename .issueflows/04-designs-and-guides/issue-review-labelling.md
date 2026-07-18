# Issue review and labelling (`/iflow-review`)

**Context.** Issue #174: help users assess how open issues should be labelled.
Today label-driven flows consume a configurable `yolo` label
([label-driven-flows.md](./label-driven-flows.md)); nothing helped *assign*
that label systematically.

**Decision.**

- New off-path skill/command **`iflow-review`**. Bare invoke lists review
  **kinds** and asks; v1 kind is **`yolo`** only.
- Fitness criteria for `yolo` reuse `/iflow-epic`'s yolo-fitness wording
  (well-specified, mechanical/pattern-following, low blast radius, test-guarded;
  umbrella / design / flag-day → no).
- Candidate set = **all open issues** (re-score already-labelled; adds are
  no-ops). v1 never removes labels.
- Missing target label → offer `gh label create` under confirm, then continue.
- Thin CLI (no judgment): `issue-flow agent label-candidates` and
  `issue-flow agent label-apply`. Judgment stays in the skill.
- Standard mode only (omitted from `modes.simple`), same class as yolo/cycle.
- Queue planning's `_yolo_from_labels` honours the resolved `yolo_label`, not a
  hardcoded `"yolo"` string.

**Alternatives considered.**

- Skill-only `gh` shell with no CLI — rejected: other off-path flows
  (status/doctor) ship deterministic helpers; apply/list are pure plumbing.
- Auto-run from `/iflow-pick` or cycle — rejected: labelling is a deliberate
  batch triage step; keep off-path.
- Filter to unlabeled-only — rejected: user wants re-score of the full open set.

**Link.** Issue #174, `issue174_plan.md`.
