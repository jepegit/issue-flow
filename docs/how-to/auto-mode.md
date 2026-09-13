---
title: Use auto mode
---

# Use auto mode

## Goal

Run an **unattended** path over a **confirmed epic**: cycle one published
stage's issues, then adversarial review between epochs, honouring a loop
budget. Auto does **not** create epics — draft, confirm, and publish first
([Create and run epics](epics.md)).

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

## Example

```text
iflow epic 42                  # draft + confirm plan
iflow epic 42 publish stage 1  # children must exist on GitHub
iflow auto 42 dry-run          # show stage + queue (no confirm)
iflow auto 42                  # overnight confirm → cycle + review
iflow auto 42 stage 2          # optional: pin a stage
iflow auto 42 loops:3          # optional: raise adversarial budget
iflow auto 42 review           # adversarial pass only
iflow auto 42 status           # print auto_status.md / epic-status
```

Auto vs cycle: `iflow cycle epic 42 stage 1` batch-yolos one stage with no
review loop. `iflow auto 42` adds adversarial review and the next-stage gate.

## Related

- [Create and run epics](epics.md) — plan + publish first
- [Run a cycle of issues](cycle.md) — batch yolo without the review loop
- [Configuration](../configuration.md) — `auto_adversarial_loops`
- [The workflow](../issue-workflow.md) — `/iflow-auto`
- Design depth (agents): `.issueflows/04-designs-and-guides/advanced-auto-mode.md`
  after `issue-flow init`
