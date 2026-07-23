# Plan — #203 Wire loop budget + ask UX into `/iflow-auto`

## Goal

After each adversarial pass, honour loop budget: increment counter; if work
remains and counter < budget, re-queue via cycle + re-run review; when budget
spent, stop and ask (accept / grant N more / abort).

## Approach

1. Extend `iflow_auto` skill: post-adversarial **Loop control** step.
2. Document manual scenario in `advanced-auto-mode.md`.
3. Tests assert budget wording / ask options / re-queue path.
4. Leave next-epoch advance to #204.

## Files

- `skills/iflow_auto/SKILL.md.j2`, `commands/iflow-auto.md.j2`
- `advanced-auto-mode.md`, workflow/docs lightly
- `tests/test_templating.py`, `test_init.py`, `HISTORY.md`
