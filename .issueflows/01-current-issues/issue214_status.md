# Status: #214 — always run graphify before planning

- [ ] Done

## What's done

- Plan accepted: opt-in `auto_graphify_on_plan` (default false).
- Wired knob through `modes.py`, `config.py`, `init.py`, `cli.py`, `agent.py`.
- Gated `/iflow-plan` skill + command templates (AST `update`, fail-soft).
- Docs (`configuration.md`) + design notes (skill-behaviour, graphify-integration).
- Tests: config/modes/templating/cli; full suite 564 passed; ruff clean.

## Remaining work

- `/iflow-close` (HISTORY + PR ready).
