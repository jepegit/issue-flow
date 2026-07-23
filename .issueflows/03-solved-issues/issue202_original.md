# Issue #202: Adversarial review skill / `/iflow-auto review`

Source: https://github.com/jepegit/issue-flow/issues/202

## Original issue text

## Context

Part of epic #169 (advanced auto mode). Stage 2 — Adversarial inter-epoch gate.

## Spec

Implement the inter-epoch adversarial check described in `advanced-auto-mode.md`: inspect stage diffs/PRs against epic + stage goals; may reopen issues and/or create inter-epoch GitHub issues with clear Spec + `Depends on` / Part of epic #<N>; record findings in `auto_status.md`.

## Acceptance criteria

- Documented criteria for the adversarial pass
- Creates/reopens via `gh` behind the overnight confirm (no extra prompts inside budget)
- Findings recorded in `auto_status.md`
- This skill-authoring issue itself is not yolo-fit

## Depends on

- #194

Part of epic #169.
