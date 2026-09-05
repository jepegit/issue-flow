# Status — Issue #241: rename iflow-init → iflow-capture; reclaim iflow-init for harness

- [x] Done

## What's done

- Plan accepted (A): capture = `iflow-capture`; cold-start `/iflow-init` off-path; no dual-meaning alias.
- Capture templates: `iflow_capture` / `iflow-capture` (former issue-capture body).
- New cold-start `iflow-init` skill + command (guides `issue-flow init` / `update`; never captures).
- Registries: `COMMAND_NAMES`, `SKILL_DIRS`, `modes.simple`, `step_profiles.toml`.
- Stage id: `STAGE_CAPTURE = "capture"`; `STAGE_INIT` back-compat alias; suggested `/iflow-capture`.
- Sweep of capture-meaning `/iflow-init` refs across templates, `init.py` post-scaffold hint, agent comment.
- Design doc `iflow-init-vs-capture.md`.
- Tests updated; **646 passed**. Scaffold re-rendered.

## Remaining work

- None for the issue. `HISTORY.md` bullet at `/iflow-close`.
