---
title: Create and run epics
---

# Create and run epics

## Goal

Break a change that is too large for one PR into **staged** GitHub issues, then
run each child through the normal lifecycle (or a yolo batch).

## Steps

1. **Anchor** — open (or already have) a GitHub issue that describes the large
   change. Or create one with `iflow issue epic <intent>`.
2. **Draft** — `iflow epic <N>`. Writes
   `.issueflows/05-epics/epic<N>_plan.md` with stages, deps, and per-issue
   yolo fitness. Drafting does **not** create GitHub issues yet.
3. **Confirm** the plan in the file (`Status: confirmed`).
4. **Publish** — `iflow epic <N> publish` or `… publish stage <k>`. One confirm
   creates that stage's issues, applies yolo labels per the plan, and updates
   the anchor task list. Re-runs are idempotent (`Published: #<M>` recorded).
5. **Execute** — `iflow pick` (epic `next_candidates` float to the top), or
   batch with `iflow cycle epic <N> stage <k>` when children are yolo-fit.
6. Advance stages only when the current stage is clear.

Flat parent/child without stages? Use `iflow split` instead.

## Related

- [The workflow](../issue-workflow.md) — `/iflow-epic`, `/iflow-cycle`
- [Use auto mode](auto-mode.md) — unattended stage + review loop
- [Fast-track a small issue](yolo.md) — single-issue hands-off
