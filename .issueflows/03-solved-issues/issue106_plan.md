# Issue #106 plan: choose flow details from issue labels

## Goal

Let issue labels drive the flow: when `/iflow-pick` selects an issue carrying the
(configurable) yolo label, run it through the `/iflow-yolo` chain instead of the
normal init → plan handoff. Add the two config knobs, and make the yolo close
step truly hands-off (merge the PR, decide the HISTORY.md update itself, pull
after switching to the default branch).

## Constraints

- Templates are the source of truth (`src/issue_flow/templates/`); never edit
  rendered copies directly. Re-render this repo's own scaffold via
  `issue-flow update` as part of implementation.
- Config keys live under `[issueflow]` in `.issueflows/config.toml`, with
  persisted-beats-env resolution (same as `caveman_default`).
- `/iflow-close` must still never delete branches (that stays in
  `/iflow-cleanup`), even when merging the PR in yolo mode.
- uv-managed project; tests via `uv run pytest`, lint via `uv run ruff check src/ tests/`.

### Prior art

- `caveman_default` / `grill_me_default` — the exact convention to mirror for
  the new keys: reader in `modes.py`, resolver + env fallback + seed +
  template-context key in `config.py`, Jinja gate in templates, README docs,
  tests in `test_modes.py` / `test_config.py` / `test_cli.py` /
  `test_templating.py`. (Found via grep + code read; `00-tools/` has nothing
  relevant.)
- `/iflow-pick` already fetches `labels` in its `gh issue list --json` call —
  no new GitHub plumbing needed.
- `write_default_config(**seed_config_values())` pass-through in
  `agent.run_config_add` means new seed keys flow into `config add`
  automatically once both sides are extended.

## Approach

### 1. Config knobs (mirror `caveman_default`)

Two new `[issueflow]` keys:

- `label_flows` (bool, **default `true`**) — allow labels to select the flow.
- `yolo_label` (string, default `"yolo"`) — the label that triggers yolo mode.

Wiring:

- `modes.py`: `read_label_flows()` / `read_yolo_label()` readers (return `None`
  when unset); extend `write_default_config()` and
  `_commented_issueflow_table()` with the two keys + comments.
- `config.py`: `resolve_label_flows()` (config.toml > `ISSUEFLOW_LABEL_FLOWS`
  env > `True`) and `resolve_yolo_label()` (config.toml >
  `ISSUEFLOW_YOLO_LABEL` > `"yolo"`). Note: `_env_flag()` hard-defaults to
  `False`; add a `default=` parameter since `label_flows` defaults **true**.
  Extend `seed_config_values()` and `template_context()` (new context keys
  `label_flows`, `yolo_label`).

### 2. Label-driven pick (templates)

In `commands/iflow-pick.md.j2` + `skills/iflow_pick/SKILL.md.j2`, gated on
`{% raw %}{% if label_flows and "iflow-yolo" in included_commands %}{% endraw %}`:

- After the user confirms the pick, check the chosen issue's labels. If one
  equals `{{ yolo_label }}` (case-insensitive), announce that the issue is
  label-marked for yolo and fold the `/iflow-yolo` consolidated confirm into
  pick's existing confirmation (one prompt total, listing the full chain).
- On yes: create the branch (Phase 2 as today), then run the `/iflow-yolo`
  chain instead of the plain `/iflow-init` + plan handoff. Yolo's own preflight
  (clean tree, passing tests) still runs and can still abort.
- When `label_flows` is false (or yolo not in the mode), render none of this.

### 3. Hands-off yolo close (templates)

- `commands/iflow-close.md.j2` + `skills/iflow_close/SKILL.md.j2`: new **`yolo`**
  input token that makes close autonomous:
  - **HISTORY.md**: decide itself — append the bullet (issue title, or `log`
    text) without showing a diff or asking; still honours `nohistory`.
  - **Merge**: after opening the PR, merge it with `gh pr merge --squash`
    (matching the repo-wide squash assumption). If GitHub refuses (branch
    protection / pending checks), fall back to `gh pr merge --squash --auto`
    and report that merge is queued. Never `--delete-branch`.
  - **Switch + pull**: after the merge, `git switch <default>` and
    `git pull --ff-only` (this already exists as step 9; in yolo it runs after
    the merge so local default includes the squash commit, and `stay` still
    opts out).
  - Local branch deletion still belongs to `/iflow-cleanup`.
- `commands/iflow-yolo.md.j2` + `skills/iflow_yolo/SKILL.md.j2`: step 5 now
  invokes `/iflow-close yolo ...` (forwarding bump/log/etc. tokens), and the
  post-run text reports "PR merged" instead of "remind to merge"; still points
  at `/iflow-cleanup` for branch deletion.

### 4. Docs

- `rules/_body.md.j2`: one short gated paragraph in the lifecycle section:
  labels can pick the flow, `yolo` label → `/iflow-yolo`, controlled by
  `label_flows` / `yolo_label` in `config.toml`.
- `README.md`: add both keys to the config-key prose and the `ISSUEFLOW_*` env
  table; fix the "three keys" / "four keys" counts in `cli.py` /
  `modes.py` docstrings and README (`config add` now writes six).

## Files to touch

- [src/issue_flow/modes.py](src/issue_flow/modes.py) — readers, `write_default_config`, commented table
- [src/issue_flow/config.py](src/issue_flow/config.py) — resolvers, `_env_flag(default=)`, seed, template context
- [src/issue_flow/cli.py](src/issue_flow/cli.py) — `config add` docstring key list
- [src/issue_flow/templates/commands/iflow-pick.md.j2](src/issue_flow/templates/commands/iflow-pick.md.j2) and [skills/iflow_pick/SKILL.md.j2](src/issue_flow/templates/skills/iflow_pick/SKILL.md.j2) — label detection + yolo dispatch
- [src/issue_flow/templates/commands/iflow-close.md.j2](src/issue_flow/templates/commands/iflow-close.md.j2) and [skills/iflow_close/SKILL.md.j2](src/issue_flow/templates/skills/iflow_close/SKILL.md.j2) — `yolo` token: auto-history, merge, switch+pull
- [src/issue_flow/templates/commands/iflow-yolo.md.j2](src/issue_flow/templates/commands/iflow-yolo.md.j2) and [skills/iflow_yolo/SKILL.md.j2](src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2) — chain `/iflow-close yolo`, updated post-run
- [src/issue_flow/templates/rules/_body.md.j2](src/issue_flow/templates/rules/_body.md.j2) — short label-flows paragraph
- [README.md](README.md) — config + env documentation
- Tests: [tests/test_modes.py](tests/test_modes.py), [tests/test_config.py](tests/test_config.py), [tests/test_cli.py](tests/test_cli.py), [tests/test_templating.py](tests/test_templating.py)
- Rendered scaffold refresh in this repo (`issue-flow update`) at the end of implementation.

## Test strategy

`uv run pytest` (plus `uv run ruff check src/ tests/`). New tests mirror the
`caveman_default` ones:

- `test_modes.py` — `read_label_flows` / `read_yolo_label` (missing file, unset
  key, explicit values); `write_default_config` emits both keys.
- `test_config.py` — resolution order (config.toml beats env beats default,
  `label_flows` unset → `True`); `seed_config_values` includes both;
  `template_context` exposes `label_flows` / `yolo_label`.
- `test_cli.py` — `config add` writes the new keys.
- `test_templating.py` — pick template contains the label-flow text when
  `label_flows=True` (with a custom label interpolated) and omits it when
  `False`; close/yolo templates mention the `yolo` token.

## Open questions

1. **Merge strategy** — plan assumes immediate `gh pr merge --squash`, falling
   back to `--auto` when blocked. OK, or always `--auto`?
2. **Scope of the label hook** — plan wires it into `/iflow-pick` only (as the
   issue describes). `/iflow-init` could additionally *note* the label when
   capturing directly, without auto-running yolo. Include that note, or keep
   init untouched?

## Status

- [x] Plan confirmed by user (implemented; see issue106_status.md)
