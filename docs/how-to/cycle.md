---
title: Run a cycle of issues
---

# Run a cycle of issues

## Goal

Land **several** small, yolo-fit issues hands-off under **one** up-front
confirm — the batch form of [Fast-track a small issue](yolo.md). Each issue
runs `capture → plan → build → close yolo` (PR squash-merged), then the tree
returns to a clean default before the next.

## Steps

1. Prerequisites: clean default branch, green project tests, issues that are
   actually small and well-specified. Label them for batching if you use the
   yolo path (`yolo` by default), or note their numbers.
2. Pick a queue spec and run `iflow cycle <spec>` (or `/iflow-cycle`):

   | Spec | Meaning |
   | --- | --- |
   | `yolo` | All open issues with the configured yolo label |
   | `label:<L>` | All open issues with that label |
   | `12 15 18` | Explicit issue numbers |
   | `epic <N> [stage <k>]` | Current (or named) stage of an epic |

   Optional tokens: `max:<n>` (default cap is 10 without it),
   `onfail:stop` / `onfail:skip` (default from config `cycle_onfail`, usually
   `stop`), `resume`, experimental `parallel:<n>`.
3. Confirm once: ordered queue, skipped/blocked items, and that each PR will
   auto-merge.
4. Cycle writes `cycle_status.md` and processes issues sequentially. It stops
   only when input is **strictly necessary** (unfixable failure, refused
   merge, ambiguous / not-actually-small scope). With `onfail:stop` (the usual
   default) it leaves you on a clean default branch; `onfail:skip` (or
   `cycle_onfail = "skip"`) parks the failed issue and continues the queue.
5. After the batch report, run `iflow cleanup` yourself to prune merged local
   branches — cycle does not auto-cleanup.

Do **not** weaken yolo safeguards to keep the queue moving. For epic stages
plus adversarial review between epochs, use [Use auto mode](auto-mode.md)
instead.

## Example

```text
iflow review yolo          # optional: label candidates first
iflow cycle yolo           # confirm list → batch merge
iflow cycle label:docs
iflow cycle 12 15 18
iflow cycle epic 42 stage 1
iflow cycle yolo max:5
iflow cleanup              # once, after the batch
```

## Related

- [Fast-track a small issue](yolo.md) — single-issue hands-off path
- [Use auto mode](auto-mode.md) — cycle a stage + adversarial review
- [Create and run epics](epics.md) — `epic <N> [stage <k>]` queues
- [After a squash merge](after-squash-merge.md) — post-batch cleanup
- [Command reference](../issue-workflow.md) — `/iflow-cycle`
