# Status — Issue #233: cleanup configurable

- [ ] Done

## What's done

- Plan accepted.
- Wired `cleanup_include_github` through `modes.py` / `config.py` / seed / CLI help / agent config-add copy.
- Softened `remind_cleanup=true` wording (remind, never auto-run) in rules + close skill/command.
- Gated leftover cleanup nudges in workflow doc + `iflow_auto`.
- Baked Phase B default + `no github` / `local only` override into cleanup skill/command + workflow section.
- Updated `docs/configuration.md`, `skill-behaviour-knobs.md`, `github-branch-audit.md`.
- Tests for resolve/seed/render/rules/cleanup templates.

## Remaining work

- Run pytest + ruff; dogfood `issue-flow update` if local skills should match (optional for this PR — templates are SoT).
- `/iflow-close` for HISTORY + ship.
