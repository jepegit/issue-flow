# Plan — Issue #174: skill for reviewing and labelling issues

## Goal

Ship an off-path, extendable `/iflow-review` skill (plus thin CLI helpers) that
reviews open GitHub issues and applies labels — starting with a **yolo** review
that tags suitable issues with the configured `yolo_label`.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; edit those,
  then dogfood via `issue-flow update` in this repo.
- Follow [skill-authoring.md](../04-designs-and-guides/skill-authoring.md):
  user-invoked, `disable-model-invocation: true`, no trigger-bait.
- Honour existing label-flow config (`label_flows`, `yolo_label`) from
  [label-driven-flows.md](../04-designs-and-guides/label-driven-flows.md).
- Off-path: never auto-dispatch from `/iflow` / start / close.
- No silent GitHub writes — consolidated confirm before any `gh issue edit`.
- Do **not** fold command↔skill dedup debt (skill-authoring known debt) into
  this PR; mirror both surfaces as other skills do today.
- v1 does **not** create new GitHub issues (create/edit “machinery” = list +
  edit labels; issue *create* stays with `/iflow-pick fix` / epic publish).

### Prior art

| Hit | Module / path | Stance |
| --- | --- | --- |
| `gh_issue_edit` / `gh_issue_list` / `gh_label_names` / `gh_label_create` | `src/issue_flow/gitutils.py` | **Reuse** for apply + existence checks |
| Sync label apply | `src/issue_flow/sync.py` (`apply_plan`) | **Mirror** confirm+edit pattern; do not couple review to sync |
| Yolo-fitness criteria | `templates/skills/iflow_epic/SKILL.md.j2` | **Reuse** wording in review skill (single shared criteria text or pointer) |
| Label-driven pick routing | `label-driven-flows.md`, pick/yolo templates | **Coexist** — review *writes* labels; pick *consumes* them |
| Off-path skill+CLI pattern | `iflow-status`, `iflow-doctor` | **Mirror** (skill + command + optional CLI fast path) |
| Surface registration | `templating.py` `COMMAND_NAMES` / `SKILL_DIRS`, `modes.toml`, `step_profiles.toml`, rules chat table | **Extend** |
| `_yolo_from_labels` hardcodes `"yolo"` | `agent.py` | **Migrate** to honour resolved `yolo_label` (case-insensitive) while touching queue/review |
| Toolbox `verify_scaffold.py` | `.issueflows/00-tools/` | **Reuse** after scaffold to assert new skill renders |

## Approach

### Name and invocation

- Skill/command stem: **`iflow-review`** (folder `iflow_review`).
- Chat forms: `iflow review`, `iflow-review`, `/iflow-review`, `/iflow review`.
- Args: optional review kind. Bare invoke → list supported kinds and ask.
  - v1 kinds: **`yolo`** only (apply configured `yolo_label`).
- Profile: **reasoning** (judgment-heavy). Off-path; **standard** mode only
  (omit from `modes.simple`, same as yolo/cycle/doctor).

### Skill flow (`yolo` kind)

1. Resolve project root / `owner/repo` (shared partial).
2. Resolve `yolo_label` (and note if `label_flows` is false — still allow
   labelling; warn that pick will not route on it until enabled).
3. Ensure label exists (`gh label list` / `gh_label_names`). If missing: offer
   create via `gh_label_create` (or `gh label create`) under confirm; stop if
   user declines.
4. List **all open issues** (`gh issue list` / `gh_issue_list_meta`) — include
   those that already carry the target label (re-score; adds are no-ops when
   already present).
5. Judge each against epic yolo-fitness: well-specified, mechanical /
   pattern-following, low blast radius, guarded by existing tests; umbrella /
   design / flag-day → no. Present a short table: `#N`, title, current labels,
   **add** / **keep** (already labelled + still fit) / **skip** + one-line
   reason. Do **not** auto-remove labels in v1 even if judgment says unfit.
6. One consolidated confirm for the **add** set → apply labels
   (`gh_issue_edit(..., add_labels=[yolo_label])` or CLI wrapper).
7. Report applied / failed / skipped / already-labelled. No removals in v1.

### CLI machinery (thin, deterministic)

Add agent-facing helpers so the skill is not shell-only soup:

- `issue-flow agent label-candidates [--kind yolo] [--json]` — all open issues
  for the kind, each tagged with whether the target label is already present
  (uses resolved `yolo_label`).
- `issue-flow agent label-apply <N> [<N>...] --label <name> [--dry-run]
  [--json]` — apply one label to many issues (no judgment; idempotent add).

Judgment stays in the skill (LLM). CLI never auto-decides fitness.

### Scaffold wiring

- Templates: `skills/iflow_review/SKILL.md.j2` + `commands/iflow-review.md.j2`.
- Register in `COMMAND_NAMES`, `SKILL_DIRS`, `step_profiles.toml`
  (`iflow_review = "reasoning"`).
- Rules (`_body.md.j2` chat table + short off-path blurb),
  `docs/issue-workflow.md.j2`, AGENTS-managed block via update.
- Design note: `.issueflows/04-designs-and-guides/issue-review-labelling.md`
  (name, kinds registry, confirm gate, reuse of epic criteria).
- Extendable kinds: skill documents a kind table; future kinds
  (`deep` / `fast` model labels, etc.) add a row + optional CLI kind — no
  rename of the skill.

### Out of scope (this PR)

- Creating GitHub issues from `/iflow-review`.
- Removing labels / bulk re-triage of already-labelled issues.
- Auto-running review from `/iflow-pick`, cycle, or epic publish.
- New review kinds beyond `yolo`.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/templates/skills/iflow_review/SKILL.md.j2` | New skill |
| `src/issue_flow/templates/commands/iflow-review.md.j2` | Matching slash command |
| `src/issue_flow/templating.py` | Register stem in `COMMAND_NAMES` / `SKILL_DIRS` |
| `src/issue_flow/step_profiles.toml` | `iflow_review = "reasoning"` |
| `src/issue_flow/templates/rules/_body.md.j2` | Chat invocation row + blurb |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Document off-path command |
| `src/issue_flow/agent.py` | `label-candidates` / `label-apply`; fix `_yolo_from_labels` to use config label |
| `src/issue_flow/cli.py` | Wire agent subcommands |
| `tests/test_cli.py` / `tests/test_templating.py` (and/or init) | Render, mirror, CLI dry-run |
| `.issueflows/04-designs-and-guides/issue-review-labelling.md` | Durable design |
| Dogfood rendered `.cursor/` + `AGENTS.md` via `issue-flow update` | After templates land |

## Test strategy

- `uv run pytest` — focus:
  - template/init: skill + command render; chat table mentions `iflow-review`;
    skill mirrors command (pattern of `test_issue_*_skill_mirrors_command`).
  - CLI: `label-candidates` JSON shape; `label-apply --dry-run` does not call
    edit; apply mocks `gh_issue_edit`.
  - `_yolo_from_labels` / queue respects non-default `yolo_label`.
- `uv run ruff check src/ tests/`.
- Optional: `uv run .issueflows/00-tools/verify_scaffold.py` after wiring.

## Open questions

_Resolved 2026-07-18 — plan accepted with:_

1. **Name:** `iflow-review` — confirmed.
2. **Missing label:** offer create under confirm, then continue — confirmed.
3. **Candidate set:** all open issues (re-score already-labelled; no auto-remove) — confirmed.
4. **CLI helpers in same PR:** yes — confirmed.
5. **simple mode:** omit — confirmed.

**Status:** accepted — ready for `/iflow-start`.
