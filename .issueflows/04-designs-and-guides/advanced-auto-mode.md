# Advanced auto mode

**Issue:** [#169](https://github.com/jepegit/issue-flow/issues/169) (epic) /
[#191](https://github.com/jepegit/issue-flow/issues/191) (this contract)
**Status:** decided 2026-07-23 (Stage 1 design).

## Context

Want an unattended path for **large** changes: thorough planning, sequential
epochs of manageable issues, yolo execution per issue, and an adversarial check
between epochs — without inventing a second lifecycle outside issue branches +
PRs.

Scaffold **modes** (`standard` / `simple`) are unrelated; this is an
orchestration flow. See [modes.md](./modes.md).

## Decisions

### Epochs = epic stages

v1 maps **epoch** → `/iflow-epic` **Stage**. No separate epoch file format.
Guiding docs live in `epic<N>_plan.md` (Goal / Constraints / Stage Goal /
per-issue Spec).

### Goals at three levels

| Level | Where |
|-------|--------|
| Epic | `## Goal` in `epic<N>_plan.md` |
| Epoch / stage | Explicit **Stage Goal** (or stage paragraph that states the goal) |
| Issue | Spec includes **Goal:** (crisp acceptance someone else can verify) |

### Overnight confirm contract

One up-front confirm before unattended run. Preconditions:

- `epic<N>_plan.md` is `Status: confirmed`
- Working tree clean on the default branch
- Project tests green

After confirm: no mid-run prompts until a **stop condition** (below) or the
adversarial **loop budget** is exhausted.

### Orchestrator surface

Off-path skill/command **`/iflow-auto`** (Stage 1 skeleton; Stage 2 adds the
adversarial gate). Composes:

1. Select earliest unfinished published stage of epic `<N>`
2. Run `/iflow-cycle epic <N>` for that stage (yolo per issue)
3. Adversarial review (Stage 2)
4. Advance or stop per loop budget

`/iflow-cleanup` stays out-of-band (same as yolo/cycle).

### Adversarial loop budget

| Knob | Default | Notes |
|------|---------|--------|
| `[issueflow] auto_adversarial_loops` | `2` | Baked at `issue-flow update`; env `ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS` |

**Trailing override** on `/iflow-auto`: `loops:<n>` (positive integer) for this
run only. Precedence: trailing > config > default `2`.

After each inter-epoch adversarial pass, if work remains and the counter is
below the budget, re-queue and re-run adversarial. When the budget is spent,
**stop and ask**: accept current implementation / grant `N` more loops / abort.

### Durable state

`.issueflows/01-current-issues/auto_status.md` (name fixed here) records:

- epic number, current epoch/stage index
- adversarial loop count and budget
- last outcome (cycle merged / adversarial findings / stopped)

Not an `issue<N>_*` group — folder sweeps leave it alone. Archive when the
auto-run finishes (same idea as `cycle_status.md`).

### Model-class hints

Published issue bodies include **`Model: deep | fast | default`**:

- `deep` — planning, adversarial review, design-heavy specs
- `fast` — mechanical / pattern-following yolo-fit work
- `default` — use the step's baked profile

Hints are advisory for agents; Stage 1 does not enforce labels. Optional later
tie-in to `deep_model_label` / `fast_model_label` (see
[step-model-directives.md](./step-model-directives.md)).

### Stop conditions (unattended)

Same floor as `/iflow-cycle` / `/iflow-yolo`: unfixable test/lint failure,
refused merge / non-ff pull, spec not actually small, action outside the
confirmed queue. Never weaken a yolo safeguard to keep moving.

## Non-goals

- Parallel adversarial agents
- Silent confirm of novel large plans (planning still needs a confirmed epic)
- Replacing `/iflow-epic` / `/iflow-cycle` / `/iflow-yolo`
- GitLab
- Auto-running `/iflow-cleanup`

## Link

Epic plan: `.issueflows/05-epics/epic169_plan.md`.  
Knobs: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).  
Cycle: [label-driven-flows.md](./label-driven-flows.md),
[parallel-cycle.md](./parallel-cycle.md).
