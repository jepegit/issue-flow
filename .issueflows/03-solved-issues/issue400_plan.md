# Plan: graphify totally gitignored (#400)

## Goal

Add a config knob that gitignores the whole `graphify-out/` tree, and when that knob is on, make `/iflow-plan` (and epic drafting) run `issue-flow graphify` before planning so a fresh checkout still has graph output to read.

## Constraints

- Default stays off. Projects that commit `GRAPH_REPORT.md` keep doing so until they set the key and re-run `issue-flow update`.
- Templates are the source of truth. Skill and command text change in `src/issue_flow/templates/`, then `issue-flow update` bakes them.
- Precedence matches other `[issueflow]` keys: project `config.toml` > user-global > `ISSUEFLOW_*` env > default.
- Do not auto-run `graphify extract` (needs an API key). The refresh is AST `update` only.
- Missing or failing `graphify` does not block planning (same as issue #214). Report the failure and fall back to grep.
- `issue-flow update` must not run `git rm`. Gitignore does not untrack files that are already in the index.
- This plan does not flip the knob in this repo and does not untrack `graphify-out/` here. See Open questions.

### Prior art

- `auto_graphify_on_plan` (`Settings.resolve_auto_graphify_on_plan` in `src/issue_flow/config.py`, baked in `templates/skills/iflow_plan/SKILL.md.j2` and `templates/commands/iflow-plan.md.j2`). Opt-in refresh before prior-art. Default false. Missing graphify → note and continue. **Coexist:** the new key also enables that same step; the old key stays for “refresh even when the report is committed.”
- `suggest_graphify` — soft skim/rebuild nudge. Never auto-runs. Leave it.
- This repo’s `.gitignore` already ignores `graphify-out/cache/`, `graphify-out/graph.html`, and `graphify-out/graph.json`. `GRAPH_REPORT.md`, `manifest.json`, and the `.graphify_*` files stay tracked (HISTORY, repo hygiene). The new key ignores the whole directory; it does not rewrite that hand-written partial block.
- Managed gitignore pattern: `ensure_editor_gitignore` in `src/issue_flow/surfaces.py` (`# BEGIN` / `# END` markers). Mirror that for the graphify block.
- Design note in `.issueflows/04-designs-and-guides/graphify-integration.md` (issue #214): projects that gitignore `graphify-out/` can set `auto_graphify_on_plan`. This knob makes that pair one switch.
- Toolbox (`00-tools/`): nothing relevant. Graph query hit `graphify()` / `run_build()` / `Settings` (communities 5, 327, 463); no existing gitignore-all helper.

## Approach

New bool `[issueflow].graphify_gitignored`, default `false`. Env `ISSUEFLOW_GRAPHIFY_GITIGNORED`. `issue-flow config show|set` accepts it. Changing it needs `issue-flow update`.

**Gitignore.** On `init` and `update`, if the resolved value is true, upsert a managed block in the target `.gitignore`:

```
# BEGIN issue-flow graphify (generated; do not edit)
graphify-out/
# END issue-flow graphify
```

If the value is false, remove that managed block when present and leave every other line alone. If `graphify-out/` paths are still tracked, print the untrack command and do not run it:

`git rm -r --cached graphify-out`

**Plan-time refresh.** Render the existing “refresh knowledge graph” step when `auto_graphify_on_plan` **or** `graphify_gitignored` is true (one step, not two). Wording names which key is on. Same failure policy as #214. Also add that step to epic draft (`iflow_epic` skill + `iflow-epic` command), which writes a plan and today only skims `GRAPH_REPORT.md` when the file already exists. `/iflow-yolo` follows `/iflow-plan`, so it inherits the step.

**Commit guidance.** In the graphify skill/command, when `graphify_gitignored` is true, say not to commit `graphify-out/`. When false, keep today’s “the graph is fine to commit” line.

**Docs.** One row in `docs/configuration.md` and in `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`. Short note on the #214 section of `graphify-integration.md`.

## Files to touch

- `src/issue_flow/modes.py` — default, `read_graphify_gitignored`, seed/write into `config.toml` with a comment.
- `src/issue_flow/config.py` — `resolve_graphify_gitignored`, `seed_config_values`, `effective_config`, `template_context`.
- `src/issue_flow/config_ops.py` — `CONFIG_KEYS` entry (`bool`, `needs_update=True`).
- `src/issue_flow/surfaces.py` — managed gitignore upsert/remove, plus a “still tracked” note.
- `src/issue_flow/init.py` — call the gitignore helper from `init` / `update` (same place as `ensure_editor_gitignore`).
- `src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2` and `templates/commands/iflow-plan.md.j2` — gate the refresh step on either flag.
- `src/issue_flow/templates/skills/iflow_epic/SKILL.md.j2` and `templates/commands/iflow-epic.md.j2` — same refresh before epic draft.
- `src/issue_flow/templates/skills/iflow_graphify/SKILL.md.j2` and `templates/commands/iflow-graphify.md.j2` — commit guidance when the key is on.
- `docs/configuration.md`
- `.issueflows/04-designs-and-guides/skill-behaviour-knobs.md`
- `.issueflows/04-designs-and-guides/graphify-integration.md`
- Tests: `tests/test_config.py`, `tests/test_modes.py`, `tests/test_templating.py`, `tests/test_cli.py` (show payload), plus a gitignore helper test next to the existing surfaces/init tests.

## Test strategy

`uv run pytest` for the new and neighbouring tests (`test_config`, `test_modes`, `test_templating`, `test_cli`, and the gitignore helper test). `uv run ruff check src/ tests/`.

Cases:

- Resolve default `false`; persisted `true` wins over env.
- Plan skill/command: both flags false → no refresh step; only `graphify_gitignored` true → step present; both true → one step.
- Gitignore helper: true writes the managed block; false removes it and keeps unrelated lines; idempotent second write.
- `config show` includes the key.

## Open questions

1. **Coexist with `auto_graphify_on_plan`.** Recommended: yes. New key gitignores `graphify-out/` and also enables the plan/epic refresh. The old key stays for refresh without gitignore.
2. **Untrack.** Recommended: print `git rm -r --cached graphify-out` when files are still tracked. Do not run it from `update`.
3. **This repo.** Recommended: leave `.issueflows/config.toml` here at the default (`false`) and keep `GRAPH_REPORT.md` tracked. Turning the knob on in issue-flow itself is a follow-up.

Accept adopts these three recommendations.
