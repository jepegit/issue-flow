# Plan — #382 bleeding edge

## Goal

Add an opt-in knob so `/iflow-cleanup` can upgrade the installed `issue-flow`
CLI to PyPI latest, then refresh this project's scaffold (`issue-flow update`).

## Constraints

- Templates are source of truth (`src/issue_flow/templates/`). Re-run
  `issue-flow update` after changing knobs.
- Knob plumbing matches siblings (`cleanup_include_github`):
  `modes.py` default + persist + `read_*`, `Settings.resolve_*`,
  `config_ops.KNOWN_KEYS`, render context, docs, knobs design doc.
- Precedence: project `config.toml` > user-global > `ISSUEFLOW_*` env > default.
- Default **off**. Network + mutates the user-global `uv tool` install.
- Never auto-run from close / yolo / cycle. Cleanup stays explicit.
- Do not replace an **editable** `uv tool` install with PyPI latest
  (dogfood / `this-project.md` gotcha).
- `issue-flow update` must run via the **new** binary (subprocess after
  install), not in-process `run_update()` on the old code.
- One PR. Not split/epic.

### Prior art

- `cleanup_include_github` — cleanup-scoped bool + opt-in/opt-out tokens +
  bake-at-render. Mirror enable rule and confirm listing.
  (`modes.py`, `iflow_cleanup/SKILL.md.j2`, `iflow-cleanup.md.j2`)
- `/iflow-init` + `docs/how-to/for-agents.md` — already tell agents
  `uv tool upgrade issue-flow` then `issue-flow update`. This issue adds a
  **deterministic agent CLI** and a cleanup hook so agents do not freestyle.
- `issue-flow update` / `update --all` / `workspace update` — scaffold only;
  they never upgrade the package. Keep that split.
- `issue-flow agent apply-changelog` — cleanup-called agent command after a
  successful FF pull; same slot and “skip if FF failed” rule.
- Toolbox: no helper for `uv tool install`. Reuse nothing from `00-tools/`.
- Graph (home `graphify-out/`): `update()` / `run_update()` / cleanup confirm
  tests; no existing self-upgrade node.

## Approach

### Knob

`[issueflow].on_bleeding_edge` (bool, default `false`). Env:
`ISSUEFLOW_ON_BLEEDING_EDGE`. Name matches the issue example; document it
next to the `cleanup_*` row in `skill-behaviour-knobs.md` (event-hook name,
not `cleanup_*`, because it upgrades the **package**, not only cleanup
hygiene).

### Agent command

`issue-flow agent self-update [-C <project_root>] [--json]`

1. Detect current `uv tool` install. If **editable** → JSON
   `{action: "skipped", reason: "editable"}`, exit 0, print why. Do not
   `uv tool install issue-flow@latest`.
2. Else run `uv tool install issue-flow@latest` (installs if missing;
   refreshes to latest). Capture stdout/stderr + new `issue-flow --version`.
3. Then subprocess `issue-flow update -C <project_root>` (PATH binary after
   install). Honour `--skip-dep-check` so headless cleanup does not prompt.
4. JSON: `action` (`upgraded` / `skipped` / `failed`), `from_version`,
   `to_version`, `update_exit`, `notes`. Non-zero only on hard failure
   (uv missing, install failed, update failed).

Do **not** add `--all` here. Workspace cleanup upgrades the tool **once**,
then runs `issue-flow update` per member (or `workspace update` when the
walk is already at the parent). v1: command always updates the `-C` root
only; the cleanup skill sequences the walk.

### Cleanup hook

Bake into `iflow_cleanup` skill + command, same pattern as Phase B:

- Opt-in tokens (case-insensitive): `bleeding edge`, `bleeding-edge`,
  `self-update`.
- Opt-out tokens: `no bleeding`, `no bleeding-edge`, `skip self-update`.
- **Enable rule:** (`on_bleeding_edge` **or** opt-in) **and** no opt-out.

When enabled, list in the **Phase A1 consolidated confirm** (after
`git pull --ff-only`):

- `issue-flow agent self-update --json -C <home>`

Run it **after a successful FF pull**, on the **home** repo (default
branch), never inside a leftover issue worktree. If FF failed / default-sync
recovery is in play, skip (same as apply-changelog). Failure of
self-update does **not** roll back branch deletes; report and continue
Phase A2 / B.

Workspace walk: one self-update (tool is machine-global) at the start of
the walk, then existing per-member Phase A/B. Do not reinstall PyPI on
every member.

### Docs

- `docs/configuration.md` table row.
- `docs/how-to/for-agents.md` — point at the agent command as the
  scripted path; keep the manual `uv tool upgrade` recipe.
- `docs/issue-workflow.md` + template — cleanup arguments / enable rule.
- `skill-behaviour-knobs.md` — new row.
- `cli.py` / `agent.py` help blurbs that already list sibling knobs.

## Files to touch

- `src/issue_flow/modes.py` — default, `read_on_bleeding_edge`, persist on
  init/update.
- `src/issue_flow/config.py` — `resolve_on_bleeding_edge` + render/show
  payloads.
- `src/issue_flow/config_ops.py` — `KNOWN_KEYS` bool.
- `src/issue_flow/agent.py` — `run_self_update` implementation.
- `src/issue_flow/cli.py` — `agent self-update` command + help lists.
- `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2`
- `src/issue_flow/templates/commands/iflow-cleanup.md.j2`
- `src/issue_flow/templates/docs/issue-workflow.md.j2`
- `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`
- `docs/configuration.md`, `docs/how-to/for-agents.md`,
  `docs/issue-workflow.md`
- Tests: `tests/test_config.py`, `tests/test_modes.py`,
  `tests/test_templating.py`, `tests/test_cli.py`, new
  `tests/test_self_update.py` (mock `uv` / subprocess). Existing
  `test_template_cli_consistency.py` will pin `self-update` automatically.

No change to this repo's `.issueflows/config.toml` (leave opt-in).

## Test strategy

`uv run pytest` (and `uv run ruff check src/ tests/`).

- Config: default false; project/env override; `config show` / `set`.
- Templates: cleanup skill mentions `agent self-update` and enable rule
  only when knob true; tokens present either way.
- Agent: editable → skipped; mocked `uv tool install` + `issue-flow update`
  → `upgraded`; uv missing / non-zero → `failed` + non-zero exit.
- Init seed writes `on_bleeding_edge = false` like other bools.

## Open questions

None blocking. Proceed with `on_bleeding_edge` + `agent self-update` +
`uv tool install issue-flow@latest` as specified. Rename the knob to
`cleanup_bleeding_edge` only if you prefer the `cleanup_*` convention.
