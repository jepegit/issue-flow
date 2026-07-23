# Plan — Issue #191: Design doc — advanced auto mode contract

## Goal

Land the durable design contract for epic #169 advanced auto mode so later
Stage 1 issues have a named key, overnight confirm rules, and model-hint
conventions to follow.

## Approach

1. Add `.issueflows/04-designs-and-guides/advanced-auto-mode.md` covering:
   epochs = epic stages; goals at epic/stage/issue; overnight confirm;
   `auto_adversarial_loops` (default 2) + `loops:<n>` override; stop/ask UX;
   Model hints `deep|fast|default`; `auto_status.md`; non-goals; `/iflow-auto`
   name.
2. Cross-link from `skill-behaviour-knobs.md`.
3. No template/code changes in this issue.

## Files to touch

- `.issueflows/04-designs-and-guides/advanced-auto-mode.md` (new)
- `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` (link row/note)

## Test strategy

`uv run pytest` (no new tests; docs-only).
