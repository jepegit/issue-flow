# Issue #246 status — set up project for novice and new users

- [x] Done

Branch: `246-novice-onboarding`
Plan: [`issue246_plan.md`](issue246_plan.md)

## What's done

- Picked #246, branched, captured the issue, drafted and confirmed the plan.
- Recorded the five plan decisions: surface name `/iflow-setup`; the agent may
  run `uv init` / `git init` / `gh repo create` behind confirms but never
  `gh auth login` or tool installs; novice = mode subset + knob preset;
  `--mode novice` implies `skill_level = "basic"`; one PR.
- `[modes.novice]` in `modes.toml` — the guided lifecycle plus the safety nets,
  without the hands-off, batch, or decomposition surfaces.
- `NOVICE_CONFIG` preset + `seed_novice_config()` in `modes.py`; `init.py`
  seeds it on `--mode novice` (only when `config.toml` does not exist yet) and
  forces `skill_level = "basic"` unless `--skill-level` was passed explicitly.
- Registered `iflow_setup` / `iflow-setup` in `templating.py` and gave the step
  a `reasoning` profile in `step_profiles.toml`.
- New `templates/skills/iflow_setup/SKILL.md.j2` and
  `templates/commands/iflow-setup.md.j2`: read the readiness report, walk the
  blockers one at a time, then hand off to `/iflow-pick`.
- New `readiness.py` (`Blocker` / `Readiness` / `probe()`) behind
  `issue-flow agent setup-status [--json]` in `agent.py` + `cli.py`.
- Membership-gated the off-path paragraphs in `templates/rules/_body.md.j2` so
  a restricted mode never advertises a command it did not install.
- `docs/getting-started.md` plus links from `docs/index.md`, `README.md`,
  `docs/cli.md`, `docs/configuration.md`, and `zensical.toml` nav.
- Design note `04-designs-and-guides/novice-onboarding.md`.
- `00-tools/verify_scaffold.py` grew a fourth check group that scaffolds
  `--mode novice` and asserts the surface subset, the seeded preset, and the
  gated rule; `00-tools/README.md` updated to match.

## Verification

- `uv run pytest -q` — 665 passed.
- `uv run ruff check src/ tests/ .issueflows/00-tools/` — clean.
- `uv run .issueflows/00-tools/verify_scaffold.py` — all four groups pass.

## Deviations from the plan

- `uv` was **not** added to `REQUIRED_DEPENDENCIES` in `dependencies.py`. That
  list drives the scaffold-time dependency prompt for tools the rendered
  workflows call at runtime; `uv` is an install-time prerequisite instead. Its
  presence check and per-platform install hints live in `readiness.py`, which
  is what `/iflow-setup` consumes.

## Remaining work

None — ready for `/iflow-close`.
