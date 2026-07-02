# Issue #106 status: choose flow details from issue labels

## Done

- Config knobs added, mirroring the `caveman_default` pattern:
  - `[issueflow].label_flows` (default `true`) and `[issueflow].yolo_label`
    (default `"yolo"`) with readers in `modes.py`, resolvers + env fallbacks
    (`ISSUEFLOW_LABEL_FLOWS`, `ISSUEFLOW_YOLO_LABEL`) in `config.py`,
    seeding in `seed_config_values`, template-context keys, and
    `config add` / `write_default_config` support (now six keys).
  - `_env_flag()` gained a `default=` parameter (label_flows defaults true).
- Label-driven pick: `iflow-pick` command + skill templates route an issue
  carrying the yolo label into the `/iflow-yolo` chain with one combined
  confirmation (gated on `label_flows` and pick/yolo being in the mode).
- Hands-off yolo close: new `yolo` token in `iflow-close` command + skill
  templates — changelog written without a confirm prompt, PR merged via
  `gh pr merge --squash` (fallback `--squash --auto`), then default-branch
  switch + `git pull --ff-only`. Branch deletion still only in `/iflow-cleanup`.
- `iflow-yolo` templates chain `/iflow-close yolo` (skip merge when `draft`).
- Docs: `rules/_body.md.j2` paragraph, README config + env-var tables, fixed
  stale "three keys" counts in cli/agent docstrings.
- Tests added in `test_modes.py`, `test_config.py`, `test_cli.py`,
  `test_templating.py` — `uv run pytest`: 303 passed; `ruff check`: clean.
- Own scaffold re-rendered via `issue-flow update` (19 files refreshed).

## Remaining work

- None — closed via `/iflow-close` (commit, push, PR).

## Status

- [x] Done
