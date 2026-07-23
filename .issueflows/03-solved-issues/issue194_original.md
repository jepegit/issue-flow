# Issue #194: /iflow-auto orchestrator skill (skeleton)

Source: https://github.com/jepegit/issue-flow/issues/194

## Original issue text

## Context

Part of epic #169 (advanced auto mode). Stage 1 — Design + orchestrator skeleton.

## Spec

New off-path skill/command `/iflow-auto` (exact name in design doc) registered in `templating.py` / `modes.toml` / step profiles. Behaviour for this issue: require confirmed `epic<N>_plan.md`; select earliest stage with unpublished or unfinished published issues; run or invoke `/iflow-cycle epic <N> stage <k>` under the overnight confirm; write durable `auto_status.md` (epoch, loop count, last outcome); stub hook "after stage: adversarial (Stage 2)".

## Acceptance criteria

- Scaffold installs skill+command
- Docs/rules list it off-path
- Dry-run / status reporting works
- Does not implement real adversarial review yet
- Tests cover registration + render

## Depends on

#191, #192

Part of epic #169.
