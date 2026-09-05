# Issue #246 plan — set up project for novice and new users

Source: https://github.com/jepegit/issue-flow/issues/246

## Goal

Make the first hour with issue-flow work for someone who has barely used agentic
coding: after `uv tool install issue-flow`, one CLI command scaffolds the
project, one chat command walks them through the remaining environment setup
(new project *or* existing project), and the scaffolded defaults are tuned so
they are not dropped into the full 20-command surface.

## Constraints

- **Templates are the source of truth.** New chat surfaces go in
  `src/issue_flow/templates/`, never as hand-written `.cursor/` files.
- **The CLI stays non-interactive by default.** `issue-flow init` already has to
  run headless (`--skip-dep-check` in CI/cloud, `verify_scaffold.py`). Guided
  interaction belongs to the agent skill; the CLI only *reports* state.
- **Nothing destructive without confirmation.** `uv init` / `git init` /
  `gh repo create` / `gh auth login` all mutate the user's machine or GitHub
  account, so each runs only behind an explicit confirm.
- **Back-compat.** Existing projects that re-run `init`/`update` must not have
  their `config.toml` knobs silently rewritten.
- **Don't pre-empt #241.** #241 wants `/iflow-init` renamed (to `/iflow-this`)
  and the freed `/iflow-init` name reused for cold-starting the harness — which
  is exactly this issue's onboarding surface. Per the pick decision, #241 stays
  separate: build the surface under a **new** name and leave a note that #241
  can later alias `/iflow-init` onto it. Do not rename `/iflow-init` here.

### Prior art

- **Toolbox** (`.issueflows/00-tools/`): `verify_scaffold.py` — scaffolds a
  throwaway project and asserts rendered markers, then flips `config.toml` keys
  and re-checks. **Reuse**: extend it to cover the new surface + novice preset
  instead of writing a new end-to-end checker.
- `src/issue_flow/dependencies.py` — `Dependency` dataclass, `check_dependencies`
  (PATH only, `shutil.which`, no subprocess), `format_missing_report`,
  `prompt_or_skip`. **Mirror**: the new readiness check extends this pattern
  rather than replacing it; PATH presence stays here, *state* checks (repo,
  auth, python project) go in the new agent helper.
- `src/issue_flow/modes.py` — `Mode` dataclass + `resolve_mode` (data-driven
  from `modes.toml`, project `[modes.*]` overrides win), `SKILL_LEVELS`
  (`basic`/`standard`/`advanced`, currently only gates the
  `python-quality-tools.md` design doc), and `write_default_config(...)` with a
  fully commented `[issueflow]` table. **Reuse**: the novice preset is a set of
  values fed to the existing `write_default_config`, plus one new
  `[modes.novice]` table — no new config mechanism.
- `src/issue_flow/agent.py` — the `issue-flow agent <verb> --json` family
  (`resolve`, `preflight`, `state`, `audit`) is the established way to give a
  skill deterministic facts. **Mirror**: `agent setup-status` joins it.
- `src/issue_flow/project.py` — `find_project_root`, workspace registry helpers.
  **Reuse** for "is this already scaffolded?".
- No existing surface runs or mentions `uv init`, `git init`, or
  `gh repo create` (grep across `src/`): the bootstrap path is genuinely new.

## Approach

Three layers, in dependency order.

### 1. `issue-flow agent setup-status` (deterministic facts)

New read-only agent subcommand in `agent.py` + `cli.py`, `--json` like its
siblings. Reports, for a target directory:

| field | how |
|---|---|
| `git.installed` / `gh.installed` / `uv.installed` | `shutil.which` (reuse `dependencies.py`) |
| `git.is_repo`, `git.has_commits`, `git.default_branch`, `git.has_origin` | `git rev-parse`, `git remote get-url origin` |
| `gh.authenticated`, `gh.account` | `gh auth status` (exit code; never prompts) |
| `python.has_pyproject`, `python.project_name`, `python.has_venv`, `python.python_version_pin` | file probes for `pyproject.toml`, `.venv/`, `.python-version` |
| `issueflow.scaffolded`, `issueflow.mode`, `issueflow.skill_level`, `issueflow.editor` | `project.find_project_root` + `modes.read_*` |
| `verdict` | `ready` / `needs_setup` + an ordered `blockers` list, each with a `fix` command string |

Never mutates anything, never prompts, exits 0 even when unready (the `verdict`
carries the signal) so a skill can always parse it.

### 2. `/iflow-setup` — the guided chat onboarding

New skill (`templates/skills/iflow_setup/SKILL.md.j2`) + slash command
(`templates/commands/iflow-setup.md.j2`), registered in `SKILL_DIRS` /
`COMMAND_NAMES`. Shape:

1. Run `issue-flow agent setup-status --json`; if the CLI is missing, fall back
   to the same probes by hand.
2. Branch on **new** vs **existing** project — inferred from
   `python.has_pyproject` + `git.is_repo` + file count, then *confirmed* with
   the user rather than guessed.
3. Walk the blockers in order, one consolidated confirm per group, running only
   what the user approves:
   - `uv` missing → print install command, stop (can't self-install).
   - New project → `uv init` (name/package layout confirmed first).
   - `git.is_repo` false → `git init` + first commit.
   - `gh` missing → install hints from `dependencies.py`, stop that branch.
   - `gh.authenticated` false → tell the user to run `gh auth login` (interactive
     browser flow; the agent must not try to drive it).
   - `git.has_origin` false → offer `gh repo create --source=. --private`.
   - `issueflow.scaffolded` false → `issue-flow init` (with the novice preset
     offered, see §3).
4. Finish with a short "what to type next" summary pointing at `/iflow-issue`
   (no issues yet) or `/iflow-pick` (issues exist) — never auto-dispatch.

Off-path: never auto-dispatched by `/iflow`.

### 3. Novice-friendly defaults

Two independent axes, both already existing concepts:

- **Surface subset** — new `[modes.novice]` in `modes.toml`: the linear
  lifecycle plus the safety nets, dropping the hands-off/batch machinery.
  Included: `iflow`, `iflow-setup`, `iflow-pick`, `iflow-init`, `iflow-plan`,
  `iflow-build`, `iflow-close`, `iflow-cleanup`, `iflow-status`, `iflow-doctor`,
  `iflow-issue`, `iflow-pause` (+ `iflow_comments`, `gh_ci`).
  Excluded: `yolo`, `cycle`, `auto`, `epic`, `split`, `fix`, `review`,
  `archive`, `graphify`, `caveman`, `grill_me`, `version_bump`,
  `history_update`.
- **Knob preset** — a `NOVICE_CONFIG` value set in `modes.py` fed to the
  existing `write_default_config`, biased toward "ask me, don't chain":
  `auto_plan = false`, `auto_build = false`, `auto_close = false`,
  `label_flows = false`, `confirm_version_bump = true`,
  `confirm_changelog_update = true`, `remind_cleanup = true`,
  `caveman_default = false`, `grill_me_default = false`,
  `suggest_graphify = false`, `early_pr = false`, `skill_level = "basic"`.

Selected by `issue-flow init --mode novice`, which (only when the mode is passed
explicitly **and** `config.toml` does not yet exist) seeds the preset. Re-running
`init`/`update` on an existing project never rewrites knobs.

### 4. Docs

New `docs/getting-started.md` covering the two entry paths end to end (install
uv → install issue-flow → new vs existing project → `issue-flow init --mode
novice` → `iflow setup` in chat → first issue). Linked from `docs/index.md`,
`README.md`, and the scaffolded workflow doc. `init`'s closing hint gains a
line pointing at `iflow setup` when the project looks unready.

## Files to touch

| Path | Change |
|---|---|
| `src/issue_flow/agent.py` | add `run_setup_status` |
| `src/issue_flow/cli.py` | `agent setup-status`; `--mode novice` help text |
| `src/issue_flow/dependencies.py` | add `uv` to a recommended/known-tools list so the report can reuse the install hints |
| `src/issue_flow/modes.py` | `NOVICE_*` preset constants + seeding helper |
| `src/issue_flow/modes.toml` | `[modes.novice]` |
| `src/issue_flow/templating.py` | register `iflow_setup` / `iflow-setup` |
| `src/issue_flow/templates/skills/iflow_setup/SKILL.md.j2` | **new** |
| `src/issue_flow/templates/commands/iflow-setup.md.j2` | **new** |
| `src/issue_flow/templates/rules/_body.md.j2` | invocation-table row + one-paragraph description (membership-gated) |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | getting-started section, gated on `"iflow_setup" in included_skills` |
| `src/issue_flow/init.py` | seed novice config on explicit `--mode novice`; closing hint |
| `docs/getting-started.md` | **new** |
| `docs/index.md`, `docs/cli.md`, `docs/configuration.md`, `README.md` | link + document the new mode/command |
| `.issueflows/00-tools/verify_scaffold.py` | assert the novice mode renders the expected subset |
| `tests/test_setup_status.py` | **new** — JSON shape / verdict across tmp-dir fixtures |
| `tests/test_modes.py`, `tests/test_init.py`, `tests/test_template_cli_consistency.py` | novice mode + preset seeding + surface registration |
| `.issueflows/04-designs-and-guides/novice-onboarding.md` | **new** design note (incl. the #241 naming interaction) |

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/` (per `AGENTS.md`).

- `test_setup_status.py`: tmp dirs for bare dir / git-no-remote / full project;
  monkeypatch `shutil.which` and the `gh`/`git` subprocess wrappers so no
  network or real `gh` is needed. Assert `verdict`, `blockers` ordering, and
  that the command never raises when tools are absent.
- `test_modes.py`: `resolve_mode("novice")` yields the expected stem sets and
  rejects unknown stems; project `[modes.*]` still overrides.
- `test_init.py`: `--mode novice` on a fresh dir writes the preset knobs and
  only the novice surfaces; a second `init` on an existing `config.toml` leaves
  the knobs untouched.
- `test_template_cli_consistency.py`: the new command/skill pair stays in sync.
- Manual end-to-end: `uv run .issueflows/00-tools/verify_scaffold.py`.

## Decisions (resolved before build)

1. **Surface name: `/iflow-setup`.** A new name now; #241 may later alias
   `/iflow-init` onto it once today's capture command is renamed. #246's own
   wording (`/iflow-init`) is therefore satisfied by #241, not here.
2. **Agent may act, behind confirms.** `/iflow-setup` runs `uv init`,
   `git init`, the first commit, and `gh repo create` itself behind per-group
   confirmations. It never runs `gh auth login` (interactive browser flow — tell
   the user to run it) and never installs `uv` or `gh` (print hints, stop that
   branch).
3. **Novice = mode subset + knob preset.** Both axes, as described in §3.
4. **`--mode novice` implies `--skill-level basic`.** Accepted coupling: the
   preset sets `skill_level = "basic"`. An explicit `--skill-level` on the same
   command line still wins, so the axes stay independently addressable.
5. **One PR.** The four deliverables ship together; no split.

## Open questions

- None outstanding. Anything surfaced during `/iflow-build` gets recorded in
  `issue246_status.md` and raised before it changes the shape above.
