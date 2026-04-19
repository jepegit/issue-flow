# Status for issue #39: Expand issue-flow workflow with additional slash commands

- [x] Done

## Done so far

- Added four new command templates under `src/issue_flow/templates/commands/`:
  - `issue-plan.md.j2` — writes `issue<N>_plan.md` (Goal / Constraints / Approach / Files to touch / Test strategy / Open questions) and stops for user confirmation.
  - `issue-pause.md.j2` — updates status with **Remaining work**, moves the `issue<N>_*` group to `.issueflows/02-partly-solved-issues/`, offers a consolidated WIP-commit + switch-to-default prompt.
  - `issue-cleanup.md.j2` — owns post-merge branch hygiene (detect merge via `gh pr view`, consolidated single confirm, `git branch -d` on merged local branches including squash-merges; never `-D`).
  - `issue-yolo.md.j2` — chains `init → plan → start → close` with up-front safeguards (refuses on default, refuses with dirty unrelated changes, requires `uv run pytest` passing, single consolidated confirm). Does not chain `/issue-cleanup`.
- Added matching skill templates under `src/issue_flow/templates/skills/` (`issueflow_issue_plan`, `issueflow_issue_pause`, `issueflow_issue_cleanup`, `issueflow_issue_yolo`).
- **Strict migration** done per user decision:
  - `/issue-start` no longer plans. It reads `issue<N>_plan.md`; when missing, it offers three options (run `/issue-plan` now, proceed without a plan and note it in the status file, or abort) instead of hard-stopping.
  - `/issue-close` no longer deletes branches. Step 7 now points users at `/issue-cleanup` after the PR merges. All other close steps are unchanged.
  - The matching skills (`issueflow-issue-start`, `issueflow-issue-close`) were updated to mirror the command changes.
- Wired 8 new entries into `TEMPLATE_MANIFEST` in `src/issue_flow/templating.py` (total is now 17).
- Refreshed `docs/cursor-issue-workflow.md.j2` with the seven-command table, nine-skill table, updated end-to-end flow diagram, and a section per new command.
- Updated `rules/issueflow-rules.mdc.j2` with a **Command lifecycle** section describing the new flow and reworded the **Branch hygiene** bullet to point at `/issue-cleanup`.
- Ran `uv run issue-flow update` so the in-tree `.cursor/commands/`, `.cursor/skills/`, `.cursor/rules/`, and `docs/` files match the new templates (17 files refreshed).
- Updated `tests/test_templating.py`: bumped the manifest-count assertion (9 → 17), added coverage for every new command + skill entry, replaced the old `/issue-close` post-merge assertion with assertions against `/issue-cleanup`, and added smoke tests for the new command templates.
- Added an `## [Unreleased]` bullet to `HISTORY.md` describing the new commands and the two breaking migrations (planning out of `/issue-start`, cleanup out of `/issue-close`).
- **Added `/iflow` smart dispatcher** to soften the added complexity: it inspects focus-issue state (branch-derived `N` preferred, else single group, else ask) and dispatches to the right linear-flow command (`/issue-init`, `/issue-plan`, `/issue-start`, or `/issue-close`) based on which files exist and whether the status file is marked `- [x] Done`. Forwards trailing args verbatim. Never auto-dispatches to `/issue-pause`, `/issue-cleanup`, or `/issue-yolo`.
  - New templates: `src/issue_flow/templates/commands/iflow.md.j2` + `src/issue_flow/templates/skills/issueflow_iflow/SKILL.md.j2`.
  - Manifest grew from 17 to 19 entries; in-tree scaffold regenerated via `uv run issue-flow update`.
  - Promoted `/iflow` as the quick-start entry point in `docs/cursor-issue-workflow.md.j2` (new "Smart dispatcher" section, new row in both the commands and skills tables) and added a one-liner at the top of the **Command lifecycle** section in `rules/issueflow-rules.mdc.j2`.
  - Test coverage: bumped `test_manifest_entry_count` (17 → 19), added `/iflow` + `issueflow_iflow` to `test_manifest_has_expected_commands_and_skills`, and added `test_iflow_describes_state_machine` asserting the dispatch table mentions all four downstream commands, the `_original.md` / `_plan.md` / `- [x] Done` state keywords, and the off-path commands (as "not auto-dispatched").

## Implementation tasks from the original issue

- [x] Create Jinja2 templates for `/issue-plan.md.j2`.
- [x] Create Jinja2 templates for `/issue-pause.md.j2`.
- [x] Create Jinja2 templates for `/issue-cleanup.md.j2`.
- [x] Create Jinja2 templates for `/issue-yolo.md.j2`.
- [x] Update `cursor-issue-workflow.md` to reflect the expanded lifecycle.
- [x] Update Agent Skills to include these new playbooks.

## Tests

- `uv run pytest` — **43 passed** (bumped from 42 after adding `test_iflow_treats_branch_derived_n_as_authoritative`).

## Remaining work

None. Ready for `/issue-close` (optionally `bump minor` given this is a meaningful feature addition with two breaking behavior changes).

## Notes / decisions

- **Migration strategy**: strict (per user). `/issue-start` no longer plans, `/issue-close` no longer cleans up merged branches. Existing users must adopt `/issue-plan` and `/issue-cleanup` explicitly.
- **`/issue-implement`**: not added. Yolo chains `init → plan → start → close` (user confirmed this was loose wording in the issue body, not a fifth command).
- **Yolo naming**: kept `/issue-yolo` (user's default preference).
- **Soft-stop refinement on `/issue-start`**: added after the initial plan — when `issue<N>_plan.md` is missing, `/issue-start` asks "run /issue-plan now / proceed without / abort" rather than hard-stopping, preserving an escape hatch for trivial tasks.
- **`/iflow` scoping (post-implementation addition)**: user confirmed two narrow choices to keep the dispatcher simple:
  - **Never auto-dispatch to `/issue-cleanup`** — users run it explicitly after merge (no `gh pr view` lookup inside `/iflow`).
  - **Off-path commands stay direct** — no `/iflow pause`, `/iflow yolo`, or `--force` subcommands. `/iflow` only routes the linear `init → plan → start → close` flow.
- **`/iflow` focus-resolution refinement (post-implementation)**: step 0, rule 1 of `/iflow` now treats a branch-derived `N` as **authoritative**, not merely "used if it matches a group under `01-current-issues/`". This fixes two rough edges:
  - *Fresh branch + unrelated groups in `01-`*: on `42-fix-login` with `issue99_*` already present, `/iflow` no longer stops-and-asks; it uses `N=42` and dispatches to `/issue-init` (state A), which captures #42 and archives the unrelated group via its own sweep.
  - *Resuming paused work*: on a branch whose `issue<N>_*` lives in `02-partly-solved-issues/` or `03-solved-issues/`, `/iflow` now warns up front that `/issue-init`'s archived-issue guard will ask for an explicit re-open confirmation, instead of silently dispatching to state A.
  - Skill mirror and new test `test_iflow_treats_branch_derived_n_as_authoritative` added; scaffold regenerated; HISTORY sub-bullet updated.
