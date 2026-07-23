# Plan — #202 Adversarial review skill / `/iflow-auto review`

## Goal

Replace the Stage 1 adversarial **stub** with a real, documented inter-epoch
review path that agents run after a stage cycle: judge work against epic/stage
goals, optionally reopen or create blocker issues via `gh`, and record findings
in `auto_status.md` — all under the overnight confirm (no mid-budget prompts).

## Constraints

- Compose `/iflow-auto` + existing `gh` / epic-status surfaces; do **not** fork
  cycle/yolo or invent a parallel lifecycle.
- **Out of scope for this issue** (owned by later Stage 2 issues):
  - #203 — loop counter increment, re-queue + re-run, stop-and-ask when budget spent
  - #204 — refuse advancing to stage `k+1` while stage `k` / blockers still open
- No parallel adversarial agents. No GitLab. No auto `/iflow-cleanup`.
- Cite: `advanced-auto-mode.md`, `skill-authoring.md`.

## Approach

### 1. Document review criteria (design doc)

Extend `advanced-auto-mode.md` with an **Adversarial review** section:

| Check | Pass when | Fail → action |
|-------|-----------|---------------|
| Stage goal met | Merged PRs for the stage's published issues collectively satisfy the Stage Goal / stage paragraph | Reopen incomplete issues and/or create inter-epoch blocker issues |
| Epic goal progress | No clear regression vs epic `## Goal` / Constraints | Same |
| Spec honesty | Landed work matches each issue Spec / Goal (no silent scope cut) | Reopen with concrete remaining acceptance |
| Blast radius | No unplanned shared-file / API breaks outside the stage queue | Create blocker issue(s) with Spec + `Depends on` + `Part of epic #<N>` |

Also document **outputs**: findings list in `auto_status.md` (outcome
`adversarial_findings` | `adversarial_clear`), and that create/reopen uses
`gh issue create` / `gh issue reopen` / comment — no extra user prompts while
loop budget remains (overnight confirm already authorized writes).

### 2. Skill behaviour: `/iflow-auto` + `review` token

Keep a **single** skill (`iflow_auto`); add input token **`review`** (and
document `/iflow-auto <N> review` / `iflow auto <N> review`).

**When `review` is present** (or when the orchestrator reaches the post-cycle
gate): run the adversarial procedure below. Do **not** re-ask overnight confirm
if `auto_status.md` already records an authorized run for this epic/stage;
standalone `review` without prior overnight confirm **stops and asks** once
(same confirm shape as auto: epic, stage, that create/reopen may happen).

**Adversarial procedure (agent instructions):**

1. Resolve epic `<N>` + stage `k` from args / `auto_status.md` / `epic-status`.
2. Gather evidence (read-only first): stage issue list + states from
   `epic-status`; merged PR titles/bodies via `gh pr list` / `gh pr view` for
   those issues; epic + stage Goal text from `epic<N>_plan.md`.
3. Apply the criteria table; produce a short findings list (clear vs gaps).
4. If **clear**: update `auto_status.md` (`last_outcome: adversarial_clear`,
   findings summary); stop with “hand off to loop/advance logic (#203/#204)” —
   do **not** start the next stage here.
5. If **gaps**: for each finding, either `gh issue reopen <M>` (+ comment with
   concrete remaining work) or `gh issue create` inter-epoch blocker (Spec,
   Goal, Model: deep, Depends on, `Part of epic #<N>.`). Prefer reopen when an
   existing stage issue still owns the gap; create only for cross-cutting /
   new work.
6. Record created/reopened numbers + findings in `auto_status.md`
   (`last_outcome: adversarial_findings`).
7. **Do not** re-run cycle or ask for more loops here — leave that wording as
   an explicit handoff to #203.

### 3. Replace Stage 1 stub in orchestrator path

In `iflow_auto` Instructions: after `/iflow-cycle` finishes the stage queue,
**follow the adversarial procedure** instead of the stub sentence. Keep loop
budget / next-epoch advance as “not implemented — see #203 / #204” one-liners
so this PR stays focused.

Mirror the same in `commands/iflow-auto.md.j2`, rules blurb, and workflow doc
section 15 (adversarial is real; loop/advance still Stage 2 follow-ups).

### 4. Tests

- Render tests: skill mentions criteria / `review` / `adversarial_clear` /
  `adversarial_findings` / reopen+create; stub phrase gone.
- Design-doc presence asserted lightly via templating or a small file read test
  if we already pattern that; otherwise rely on skill text + manual doc edit.
- No live `gh` integration tests.

## Files to touch

- `.issueflows/04-designs-and-guides/advanced-auto-mode.md`
- `src/issue_flow/templates/skills/iflow_auto/SKILL.md.j2`
- `src/issue_flow/templates/commands/iflow-auto.md.j2`
- `src/issue_flow/templates/docs/issue-workflow.md.j2` (+ `docs/issue-workflow.md` if kept in sync)
- `src/issue_flow/templates/rules/_body.md.j2` (short: review is real)
- `tests/test_templating.py`
- `HISTORY.md` (on close)

## Test strategy

`uv run ruff check src/ tests/` and `uv run pytest`.

## Open questions

1. **Standalone confirm for `review`:** proposed above (ask once if no prior
   overnight auth in `auto_status.md`). OK?
2. **Inter-epoch issue label:** none in v1 (only `Part of epic #<N>.` in body),
   or add a soft label if one exists? **Recommend: none** (avoid label sprawl).
3. **Model line on created blockers:** always `Model: deep`? **Recommend: yes.**
