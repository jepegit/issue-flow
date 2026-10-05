# Plan — issue #402: hands-off mode

## Goal

Add `issue-flow mode hands-off` so a project’s skills are re-rendered for unattended work. After that, `iflow drive <N>` runs the existing drive chain with no up-front confirm and no stop for “this issue is big”. `iflow drive <short description>` (no issue yet) grills once, creates the epic anchor, then does the same. Before the epic draft and before every child `/iflow-plan`, run an AST graphify update.

## Constraints

- Templates stay the source of truth. Do not regex-rewrite installed skill files. `issue-flow update` already bakes `[issueflow]` knobs into skills; this mode uses that path.
- Do not overload scaffolding `mode` (`standard` / `novice` / `simple`, `issue-flow init --mode`). That key chooses *which* surfaces exist. Hands-off chooses *how* the unattended chain behaves. Persist `hands_off = true|false` under `[issueflow]`.
- Drive stays compose-only ([drive-mode.md](../04-designs-and-guides/drive-mode.md)). Do not fork yolo, cycle, auto, or epic.
- Safety stops stay: unfixable failure, refused merge, non-fast-forward that `sync-branch` cannot resolve, dirty product tree, user `abort` / `stop` / `cancel` / `halt`. Never weaken yolo safeguards. Never `-D` `unique_work`. Never Phase B. Never rebase or force-push the default branch.
- “Big issue” is not a stop. Do not offer `/iflow-split` mid-drive. `yolo: no` stays a lane (`cycle_nonyolo`), not a halt.
- Interactive commands stay gated: `/iflow-pick`, `/iflow-plan` Accept, `/iflow-build`, non-yolo `/iflow-close`, `/iflow-doctor`.
- Per project (cwd). Not a user-global switch that rewrites every registered repo.
- Hands-off graphify is AST `update` only (`issue-flow graphify`). Never `extract` (that needs an LLM key). A missing or failing `graphify` is reported and planning continues on grep, same as issue #214. It is not a new drive stop.
- Do not commit `graphify-out/graph.json`, `graph.html`, or `cache/`. The run is a local input to planning.

### Prior art

- `issue_flow.modes` + `modes.toml` — scaffolding surface sets. Coexist. New knob beside them, not a new `[modes.hands-off]` id.
- [skill-behaviour-knobs.md](../04-designs-and-guides/skill-behaviour-knobs.md) — bake booleans at `update` (`auto_plan`, `grill_me_default`). Mirror that (`config.py` `template_context`, `modes.py` read/write, `config_ops.py` key spec).
- [drive-mode.md](../04-designs-and-guides/drive-mode.md) + `iflow_drive` — one confirm, then epic → auto → cleanup. Extend the confirm contract when `hands_off` is baked; do not add a second orchestrator.
- `cycle_nonyolo` (issue #386) — already stops treating `yolo: no` as a halt. Reuse; do not re-decide merge policy.
- `grill-me` skill — description path interviews with this, then stops grilling.
- `/iflow-issue epic` — description path creates the anchor the same way (problem / spec / acceptance). Drive still never invents a second anchor format.
- `.issueflows/00-tools/verify_scaffold.py` — optional end-to-end render check after the knob exists. No new toolbox script.
- `auto_graphify_on_plan` (issue #214) and `graphify_gitignored` (issue #400) — already run `issue-flow graphify` before `/iflow-plan` prior-art and once before an epic draft. Coexist. Hands-off forces that same refresh even when both knobs are false. Those knobs still own the refresh for interactive plan/epic when hands-off is off. See [graphify-integration.md](../04-designs-and-guides/graphify-integration.md).

## Approach

1. **CLI.** `issue-flow mode` with no args prints `hands_off` for the cwd project. `issue-flow mode hands-off` sets `hands_off = true` and runs the same render as `issue-flow update` (skills, commands, rule). `issue-flow mode standard` (alias `off`) sets `hands_off = false` and re-renders. Turning it on prints what the next `iflow drive` may do (auto-merge per `cycle_nonyolo`, local `-d`/`-D` under the existing drive cleanup rules) and asks once unless `--yes`.

2. **Bake.** Default `hands_off = false`. Env `ISSUEFLOW_HANDS_OFF` sits below project config, same precedence as `grill_me_default`. Jinja `{% if hands_off %}` only. Off-state skill text stays as it is today.

3. **Graphify before every plan.** When `hands_off` is on, run `issue-flow graphify -C <project_root>` (AST `update`) immediately before the epic draft and immediately before each child `/iflow-plan` (each issue inside a stage, after earlier issues have landed). Then prior-art uses the fresh report. This is baked into `iflow_epic` and `iflow_plan`, so drive, auto, cycle, and yolo pick it up without a separate call. Off-state text is unchanged unless `auto_graphify_on_plan` or `graphify_gitignored` is already on.

4. **`iflow drive <N>` when hands-off.** First line tells the user hands-off mode is on. Skip the drive confirm (the mode switch was the authorization). Still draft → publish-all → `/iflow-auto` each stage → final review → local cleanup → `/iflow-status`. Child skills (epic publish, auto overnight, cycle queue, yolo consolidated confirm, cleanup A1/A2 with the `drive` token) get one baked sentence: this confirm is already authorized, do not ask. Budget ask (accept / grant / abort) becomes **accept**: record `accepted`, do not re-queue, continue to the epoch gate and final review. Abort tokens still stop at the next boundary.

5. **`iflow drive <short description>` when hands-off.** Input that is not a positive integer is a feature description. Notify hands-off. Run grill-me on that description until the spec is settled. Create one epic-anchor GitHub issue (same shape as `/iflow-issue epic`) with no second confirm. Then run step 4 on that number. The epic draft and each later child plan still get step 3. When hands-off is off, a non-integer still stops and asks for `<N>` (today’s rule).

6. **Direct unattended commands.** While the knob is on, `/iflow-yolo`, `/iflow-cycle`, and `/iflow-auto` also skip their own up-front confirms, and auto’s budget ask auto-accepts. They are the same rendered text drive composes. Their plan steps also run step 3. Pick / plan Accept / build / ordinary close do not skip confirms. Interactive `/iflow-plan` does run the graphify refresh while hands-off is on.

7. **Docs.** New `.issueflows/04-designs-and-guides/hands-off-mode.md` (context, decision, alternatives, link to #402). Update the drive section in the workflow doc template and the configuration knob table. `drive-mode.md` and `graphify-integration.md` get a short pointer, not a rewrite.

## Files to touch

- `src/issue_flow/cli.py` — `mode` command.
- `src/issue_flow/modes.py` — default, read/write `hands_off`, seed it in config writers.
- `src/issue_flow/config.py` — resolve + `template_context`.
- `src/issue_flow/config_ops.py` — `issue-flow config set hands_off`.
- `src/issue_flow/templates/skills/iflow_drive/SKILL.md.j2` and `commands/iflow-drive.md.j2` — description input, skip confirm, budget auto-accept, notify.
- `src/issue_flow/templates/skills/iflow_plan/SKILL.md.j2`, `commands/iflow-plan.md.j2`, `skills/iflow_epic/SKILL.md.j2`, `commands/iflow-epic.md.j2` — graphify refresh when `hands_off`, even if the other graphify knobs are off.
- `src/issue_flow/templates/skills/iflow_auto/SKILL.md.j2`, `iflow_cycle`, `iflow_yolo`, `iflow_cleanup` (and matching command templates where they repeat the confirm) — one authorized-already sentence when `hands_off`.
- `src/issue_flow/templates/docs/issue-workflow.md.j2`, `docs/configuration.md` (or its template if the page is generated), `templates/rules/_body.md.j2` if the lifecycle blurb must mention the mode.
- `tests/test_cli.py`, `tests/test_config.py`, `tests/test_modes.py`, `tests/test_templating.py` — knob round-trip and rendered sentences for on and off.
- `.issueflows/04-designs-and-guides/hands-off-mode.md`, short pointer in `drive-mode.md`, `skill-behaviour-knobs.md`, and `graphify-integration.md`.

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/`.

New cases: default off; config and env resolution; `mode hands-off --yes` writes the key and a rendered drive skill contains the skip-confirm sentence; `mode standard --yes` removes it; description-path wording exists only when on; budget auto-accept wording exists only when on; off-state drive still requires `<N>` and the drive confirm. With `hands_off` on and both graphify knobs off, rendered plan and epic skills contain the AST refresh and do not mention `extract`. With `hands_off` off, that sentence is absent unless `auto_graphify_on_plan` or `graphify_gitignored` is on.

## Open questions

- None. Unattended chain skips confirms; interactive plan Accept / pick / close still ask; budget exhaustion auto-accepts; hands-off runs AST graphify before the epic draft and before each child plan, and continues if graphify is missing. **Revise** if direct `iflow yolo` / `iflow cycle` should keep their confirms unless entered from drive, if budget exhaustion should still ask, or if a failed graphify should stop the drive.
