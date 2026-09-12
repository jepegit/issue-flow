---
title: Use auto mode
---

# Use auto mode

## Goal

Run an **unattended** path over a **confirmed** epic stage: cycle the stage's
issues, then adversarial review between epochs, honouring a loop budget.

## Steps

1. Prerequisites: epic plan `Status: confirmed`, published stage with open
   children, clean default branch, green project tests.
2. Run `iflow auto <N>` (or `/iflow-auto <N>`). Confirm once up front
   (overnight contract).
3. Orchestrator selects the earliest unfinished published stage, drives it via
   `/iflow-cycle`, records `auto_status.md`, then runs adversarial review
   (`review` token).
4. On findings: re-queue within the loop budget (default **2**, override
   `loops:<n>` or `[issueflow].auto_adversarial_loops`), or **stop and ask**
   (accept / grant more loops / abort).
5. Advance to stage `k+1` only when stage `k` is clear. Otherwise the run ends
   `epoch_gated`.
6. `/iflow-cleanup` stays out-of-band — run it yourself after merges.

Stop conditions (failed tests, refused merge, ambiguous scope) abort the whole
auto run and leave you on the default branch when possible.

## Related

- [Create and run epics](epics.md) — plan + publish first
- [Configuration](../configuration.md) — `auto_adversarial_loops`
- [The workflow](../issue-workflow.md) — `/iflow-auto`
- Design depth (agents): `.issueflows/04-designs-and-guides/advanced-auto-mode.md`
  after `issue-flow init`
