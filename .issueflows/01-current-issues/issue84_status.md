# Issue #84 — status

- [ ] Done

## What's done

- Issue captured (`issue84_original.md`) and plan confirmed (`issue84_plan.md`).
- Branch `cursor/84-archive-issueflow-a0b3` created off `main` (cloud-mandated
  naming instead of the usual `84-<slug>` style).

## Remaining work

- `tracking.plan_archive` / `apply_archive` + `gitutils.head_sha`.
- `agent.run_archive` + `issue-flow agent archive` CLI subcommand.
- New templates: `skills/iflow_archive/SKILL.md.j2`, `commands/iflow-archive.md.j2`.
- Registration: `templating.py`, `modes.toml`, `rules/_body.md.j2`,
  `docs/issue-workflow.md.j2`.
- Unit tests; full test/lint/scaffold verification; manual end-to-end in a
  throwaway project.
- Re-render this repo's own surfaces via `issue-flow update`.
