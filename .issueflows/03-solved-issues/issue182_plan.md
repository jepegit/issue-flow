# Plan — Issue #182: More config settings

## Goal

Add eight new `[issueflow]` knobs that bake into skill/rule templates on
`issue-flow update`, so projects can tweak lifecycle nudges and close/yolo/cycle
behaviour without editing templates by hand. **Accepted set: knobs 1–7**
(user confirmed 2026-07-19); **knob 8 `auto_close`** added 2026-07-19.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; re-render via
  `issue-flow update`.
- Match existing knob pattern: `DEFAULT_*` in `modes.py` → `read_*` →
  `Settings.resolve_*` → `seed_config_values` / `template_context` →
  `write_default_config` / `_commented_issueflow_table` → Jinja `{% if %}` /
  `{{ }}` in skills/commands/rules/docs → tests + `docs/configuration.md` +
  design note under `04-designs-and-guides/`.
- Bake at render time (no runtime `config.toml` reads by agents) — same as
  `label_flows` / `checks_watch_minutes` ([label-driven-flows.md](../04-designs-and-guides/label-driven-flows.md)).
- Do not change off-path / never-auto-dispatch semantics; knobs only gate
  *reminders*, *defaults*, or *parameterised* commands already present.
- Scope = accepted knobs only; no drive-by refactors of the command/skill
  duplication debt (#117 follow-up).

### Prior art

- Knob plumbing: `Settings` in [`config.py`](../../src/issue_flow/config.py);
  readers/writers in [`modes.py`](../../src/issue_flow/modes.py)
  (`write_default_config`, `_commented_issueflow_table`); template context keys
  already include `caveman_default`, `label_flows`, `yolo_label`,
  `checks_watch_minutes`, `step_directives`, …
- Soft suggestions already exist (hardcoded): `/iflow-close` steps 10–11 cleanup
  reminder; `/iflow` state-D cleanup hint; cycle batch-report cleanup reminder;
  rules graphify “may suggest” language.
- Hardcoded parameters: yolo merge `--squash`; cycle queue cap `10`.
- Toolbox: `verify_scaffold.py` — extend markers if new render gates matter.
- Graph: Communities around Settings / modes / config (God Nodes: Settings,
  `write_default_config`) — mirror those modules.

## Accepted knobs

| # | Key | Type | Default | Behaviour when enabled / set |
|---|-----|------|---------|------------------------------|
| 1 | `remind_cleanup` | bool | `true` | `/iflow-close`, `/iflow` (state D), `/iflow-cycle` batch report remind user to run `/iflow-cleanup` after merge. **`false`:** omit those reminders (cleanup skill still exists). |
| 2 | `suggest_graphify` | bool | `true` | Soft hints: skim `GRAPH_REPORT.md` / suggest rebuild after large structural changes (`/iflow-start`, `/iflow-close`, rules graphify section). **`false`:** omit suggestions; never auto-runs graphify either way. |
| 3 | `auto_switchback` | bool | `true` | After PR open/update, `/iflow-close` switches to default when tree clean (unless `stay` token). **`false`:** default is stay-on-branch (same as always passing `stay`). |
| 4 | `pr_merge_method` | str | `"squash"` | Yolo close merge flag: `squash` → `--squash`, `merge` → `--merge`, `rebase` → `--rebase`. Invalid values fall back to squash. Rules “assume squash-merges” wording gated/adjusted when not squash. |
| 5 | `cycle_max_issues` | int | `10` | `/iflow-cycle` cap before requiring explicit `max:<n>` / larger-run confirm. Non-positive → fall through to default. |
| 6 | `confirm_version_bump` | bool | `false` | When **`true`**, `/iflow-close` (non-yolo) asks once whether to bump if user did not pass a bump token. **`false`:** current behaviour (bump only when requested). |
| 7 | `ruff_autofix` | bool | `true` | When ruff is present, `/iflow-start` / `/iflow-close` run `ruff check --fix` + `ruff format`. **`false`:** skip autofix (tests/lint still may run as project requires). |
| 8 | `auto_close` | bool | `false` | When **`true`**, `/iflow-start` (and `/iflow-fix` end) chain into `/iflow-close` when ready to ship. Close keeps its own confirms. Gated on `iflow_close` in mode. No conflict with other knobs. |
| 9 | `confirm_changelog_update` | bool | `true` | When **`true`**, show HISTORY diff and confirm once before write. **`false`:** write without asking (like yolo history). `nohistory` still skips. |

### Out of scope (unchanged)

- `history_on_close` — already covered by `nohistory` / `yolo` decide-yourself path.
- `offer_epic_stage_gate` — rare; keep always-on offer.
- Moving env-only path knobs (`ISSUEFLOW_DIR`, …) into `config.toml` — out of
  scope; those are environment-only by design.

## Approach (after knob accept)

1. Add `DEFAULT_*` + `read_*` in `modes.py`; wire through `write_default_config`,
   `_commented_issueflow_table`, `seed_config_values`, `template_context`,
   `resolve_*` on `Settings`.
2. Gate / parameterise the matching Jinja in skill + command templates (and
   `_body.md.j2` / workflow doc where the same sentence appears).
3. Env fallbacks: `ISSUEFLOW_<KEY>` with same precedence as siblings
   (`config.toml` > env > default).
4. Tests: resolve/seed/read round-trips; template render assertions for true/false
   (or squash vs merge) branches; extend `verify_scaffold.py` only if a marker
   is cheap.
5. Docs: `docs/configuration.md` (+ template if any); short design note
   `04-designs-and-guides/skill-behaviour-knobs.md`.
6. Dogfood: set any non-default knobs in this repo’s `config.toml` only if useful;
   run `issue-flow update` so local skills match.

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/modes.py` | Defaults, readers, `write_default_config`, comments |
| `src/issue_flow/config.py` | `resolve_*`, `seed_config_values`, `template_context` |
| `src/issue_flow/cli.py` / `agent.py` | Help text listing new keys (if present today) |
| `src/issue_flow/templates/skills/iflow_{close,iflow,cycle,start}/…` | Jinja gates / `{{ pr_merge_method }}` / `{{ cycle_max_issues }}` |
| Matching `templates/commands/*.md.j2` | Keep in sync with skills |
| `templates/rules/_body.md.j2`, `templates/docs/…` | Same wording |
| `tests/test_config.py`, `test_modes.py`, `test_templating.py` (as needed) | Coverage |
| `docs/configuration.md` | Document keys |
| `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md` | Decision record |
| `.issueflows/00-tools/verify_scaffold.py` | Optional marker checks |

## Test strategy

- `uv run pytest` — focus `tests/test_config.py`, `tests/test_modes.py`,
  `tests/test_templating.py`, `tests/test_cli.py` as touched.
- Spot-check: scaffold or `verify_scaffold.py` after flipping a bool in throwaway
  `config.toml` + `update`.

## Open questions

- None — knobs 1–7 accepted; naming stays `pr_merge_method`.
