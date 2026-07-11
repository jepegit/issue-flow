# Plan — Issue #141: /iflow-cycle skill — sequential hands-off issue loop

Part of epic #145 (cycling mode), stage 1. Depends on #140 (stacked on the
queue branch). New off-path surface, standard mode only.

## Goal

`/iflow-cycle <queue-spec>` processes **many** issues hands-off with a single
up-front confirmation, running each through the existing yolo chain, and
interrupting the user only when strictly necessary.

## Constraints

- Reuse the yolo chain **verbatim**, including its safeguards — a safeguard
  failure is a **stop condition**, never a skipped guard.
- One consolidated confirm up front; no per-issue confirms.
- Default failure policy: **stop the cycle** on the first stop condition,
  report progress, land on a clean default branch. (onfail:skip is #142.)
- Cap: refuse queues longer than a documented max (10) without `max:<n>`.
- New surface must register everywhere (COMMAND_NAMES, SKILL_DIRS,
  step_profiles, off-path enumerations) and be standard-mode-only.

## Approach

1. Register `iflow-cycle` / `iflow_cycle` (templating, step_profiles =
   reasoning).
2. New `templates/skills/iflow_cycle/SKILL.md.j2` (+ command twin): queue
   spec forms (numbers / `label:<L>` / `epic <N> [stage <k>]`) resolved via
   `issue-flow agent queue --json`; up-front consolidated confirm listing
   the ordered queue and skipped/blocked; per-issue yolo chain; the
   **strictly-necessary-input rule** (explicit stop-condition list); stop
   -on-fail policy; batch report; the cap.
3. Off-path enumerations (dispatcher skill + command, rules body, workflow
   doc table).
4. Tests (test_init: cycle-surface content, standard-mode-only), HISTORY,
   scaffold regen.

## Test strategy

Template-contract tests (this slice is prompt-side; the queue CLI it drives
is already tested under #140).
