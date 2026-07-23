# Epic #169: advanced auto mode

Anchor: https://github.com/jepegit/issue-flow/issues/169
Status: confirmed

## Goal

Ship an **unattended large-change flow** that: (1) plans with guiding documents
split into sequential **epochs** (mapped to epic **stages**) of manageable
issues with goals at epic / epoch / issue level; (2) executes each issue via the
normal lifecycle under yolo; (3) runs an **adversarial review** between epochs
that may reopen work or spawn inter-epoch blockers; (4) caps adversarial loops
(default 2, overridable) and asks the user when the budget is spent; (5) records
**model-class hints** on published issues so cheap models handle simple work.
Done when a project can run `/iflow-auto <epic>` (name TBD in Stage 1) overnight
on a confirmed epic with durable resume state, without inventing a parallel
lifecycle outside issue branches + PRs.

## Constraints

- **Compose, don't fork.** Reuse `/iflow-epic` (plan + publish), `/iflow-cycle`
  (stage queue → yolo), `/iflow-yolo` (leaf). New surface is a thin orchestrator
  + adversarial gate, not a second cycle/yolo.
- **Epochs = epic stages** for v1 (naming alias in docs/skills). No separate
  epoch file format.
- **Epics decompose into** the normal single-issue lifecycle; every auto-run
  issue still gets a branch + PR.
- `/iflow-cleanup` stays out-of-band (same as yolo/cycle).
- Overnight contract: **one up-front confirm** (plan already `Status: confirmed`,
  clean tree, tests green) then hands-off until loop budget ask or hard stop.
- Planning / adversarial review = **reasoning** profile; leaf yolo issues honour
  their Model hint (`deep` / `fast` / `default`).
- Cite: [modes.md](../04-designs-and-guides/modes.md) (scaffold modes ≠ this
  flow), [label-driven-flows.md](../04-designs-and-guides/label-driven-flows.md),
  [parallel-cycle.md](../04-designs-and-guides/parallel-cycle.md),
  [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md),
  [step-model-directives.md](../04-designs-and-guides/step-model-directives.md).
- Non-goals for this epic: parallel adversarial agents; GitLab; replacing
  `/iflow-epic` draft confirm with fully silent plan generation (may appear under
  Later).

## Stage 1 — Design + orchestrator skeleton

Prove a durable auto-run can drive **confirmed epic stage → cycle → advance**
with goals + model fields documented and config for the loop budget in place
(even if the adversarial step is still a stub/TODO).

### Issue: Design doc — advanced auto mode contract

- Spec: Add `.issueflows/04-designs-and-guides/advanced-auto-mode.md` defining:
  epochs = epic stages; required Goal text at epic / stage / issue; overnight
  confirm contract; adversarial loop budget (default 2) and override tokens /
  config key; stop/ask UX when budget spent; model-class hints on published
  issues (`deep` / `fast` / `default`); resume via `auto_status.md` (or named
  equivalent); explicit non-goals. Acceptance: design doc merged; knobs table
  cross-linked from `skill-behaviour-knobs.md`; cited by later Stage 1 issues.
- Depends on: none
- yolo: no — product/policy decisions; needs human confirm
- Published: #191

### Issue: Config knobs for adversarial loop budget

- Spec: Add `[issueflow]` key (name per design doc, e.g.
  `auto_adversarial_loops`, default `2`) with env override, bake into templates
  at `issue-flow update`, document in config guide / knobs table. Trailing /
  wording overrides (e.g. `loops:5`) specified in design doc and rendered into
  the auto skill. Acceptance: round-trip tests for resolve/seed/write; rendered
  skill mentions default and override; `issue-flow update` bakes the value.
- Depends on: stage 1 issue 1
- yolo: yes — follows existing skill-behaviour-knobs pattern once the key name
  is fixed in the design doc
- Published: #192

### Issue: Epic plan markers — Stage Goal + issue Goal/Model

- Spec: Extend `/iflow-epic` plan structure (skill + `epicplan.py` as needed)
  so each Stage has an explicit **Goal** line/paragraph and each Issue Spec
  includes **Goal:** and **Model: deep|fast|default** (publish copies Model into
  the GitHub issue body). Acceptance: parser/tests accept the markers;
  `publish` bodies include Goal + Model; old plans without markers still parse;
  skill docs updated.
- Depends on: stage 1 issue 1
- yolo: no — parser + publish contract; medium blast radius
- Published: #193

### Issue: `/iflow-auto` orchestrator skill (skeleton)

- Spec: New off-path skill/command `/iflow-auto` (exact name in design doc)
  registered in `templating.py` / `modes.toml` / step profiles. Behaviour for
  this issue: require confirmed `epic<N>_plan.md`; select earliest stage with
  unpublished or unfinished published issues; run or invoke `/iflow-cycle epic
  <N> stage <k>` under the overnight confirm; write durable `auto_status.md`
  (epoch, loop count, last outcome); stub hook "after stage: adversarial
  (Stage 2)". Acceptance: scaffold installs skill+command; docs/rules list it
  off-path; dry-run / status reporting works; does not implement real
  adversarial review yet; tests cover registration + render.
- Depends on: stage 1 issue 1, stage 1 issue 2
- yolo: no — new lifecycle surface; orchestration judgment
- Published: #194

### Issue: Stage 1 tests and HISTORY

- Spec: Add/extend pytest coverage for new knobs, epic markers (if landed), and
  `/iflow-auto` scaffold registration; append HISTORY Unreleased bullet when
  closing. Acceptance: `uv run pytest` green; HISTORY bullet present in the
  close commit.
- Depends on: stage 1 issue 2, stage 1 issue 3, stage 1 issue 4
- yolo: yes — mechanical once surfaces exist
- Published: #195

## Stage 2 — Adversarial inter-epoch gate

Prove that after a stage's cycle completes, an adversarial pass can reopen or
spawn blockers, honour the loop budget, and only then allow the next epoch.

### Issue: Adversarial review skill / `/iflow-auto review`

- Spec: Implement the inter-epoch adversarial check described in
  `advanced-auto-mode.md`: inspect stage diffs/PRs against epic + stage goals;
  may reopen issues and/or create inter-epoch GitHub issues with clear Spec +
  `Depends on` / Part of epic #<N>; record findings in `auto_status.md`.
  Acceptance: documented criteria; creates/reopens via `gh` behind the
  overnight confirm (no extra prompts inside budget); yolo-fitness `no` for the
  skill authoring issue itself.
- Depends on: stage 1 issue 4
- yolo: no — highest product risk; judgment-heavy

### Issue: Wire loop budget + ask UX into `/iflow-auto`

- Spec: After each adversarial pass, increment loop counter; if issues remain
  open/reopened and counter < budget, re-queue those issues via cycle and
  re-run adversarial; when budget exhausted, **stop and ask** (accept current /
  grant N more loops / abort) per design doc; honour config + trailing
  overrides. Acceptance: unit/contract tests or scaffold assertions for budget
  wording; manual scenario documented in design doc.
- Depends on: stage 1 issue 2, stage 2 issue 1
- yolo: yes — once adversarial skill + design UX exist, wiring is patterned

### Issue: Gate next epoch on clear queue

- Spec: `/iflow-auto` must not start stage `k+1` while stage `k` has open
  published issues or open inter-epoch blockers (reuse `issue-flow agent queue`
  / `epic-status` blockers). Acceptance: epic-status/queue based gate covered
  by tests or deterministic CLI checks; design doc updated.
- Depends on: stage 2 issue 1
- yolo: yes — mostly composition of existing queue/epic-status

## Later (unstaged)

- Enforce Model hints in publish + announce during pick/cycle (deep/fast labels).
- Safer overnight: resume across agent sessions, max stages cap, refuse dirty tree.
- Optional planning preflight: deep model drafts epic plan then **one** confirm
  before unattended run (do not silent-confirm novel large plans).
- Optional `auto` label entry via `/iflow-pick` (defer; avoid label sprawl).
- Parallel independent issues inside an epoch (reuse parallel-cycle; low priority).
