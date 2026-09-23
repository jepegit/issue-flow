# Archived issues — 2026-09-23

Pre-archive git ref: `d81129c759b2eca1a05d6ecd4de206c0c5d5950e`
Recover any archived file with `git show <sha>:<path>` (or browse `git log -- <path>`).

## Issue #317: Help agents watch until a PR is merge-ready

- Source: https://github.com/jepegit/issue-flow/issues/317
- Archived files: issue317_original.md, issue317_plan.md, issue317_status.md
- Summary: Added `issue-flow agent pr-ready [N] [--watch]` to classify and poll PR merge-readiness without merging. Wired `classify_pr_ready` / `run_pr_ready` and optional `gh_pr_view` rollup fields; tests cover ready, optional UNSTABLE, blocked, missing, and watch timeout. gh-ci and close now offer `pr-ready --watch`; docs and design notes updated.

## Issue #315: Iterative fixes: agent-facing help

- Source: https://github.com/jepegit/issue-flow/issues/315
- Archived files: issue315_original.md, issue315_status.md
- Summary: `/iflow-fix` session for agent-facing docs. Added `docs/how-to/for-agents.md` and `docs/llms.txt` covering package upgrade vs scaffold refresh, global init, and workspace; `/iflow-init` and getting-started now point at them. Closed as 0.5.6.post2.

## Issue #313: Iterative fixes: workspace docs

- Source: https://github.com/jepegit/issue-flow/issues/313
- Archived files: issue313_original.md, issue313_status.md
- Summary: `/iflow-fix` session that made the parent-folder workspace recipe findable: `docs/how-to/workspaces.md` plus wiring into nav, getting-started, CLI reference, editors, README, workflow doc, and `/iflow-init`. CLI reference was regrouped into glance tables; Typer shell completion landed as `issue-flow --install-completion`. Closed as 0.5.6.post1.

## Issue #310: need a global iflow initialisation command

- Source: https://github.com/jepegit/issue-flow/issues/310
- Archived files: issue310_original.md, issue310_plan.md, issue310_status.md
- Summary: Shipped `issue-flow workspace bootstrap` (classify-only by default; `--yes` inits unscaffolded own-git children then `workspace init`). Classification skips non-git, enclosing, and symlink children and never creates a parent `.issueflows/` or `git init`s. `/iflow-init` now has a parent-folder branch and is a `both` stem; related design docs were updated.

## Issue #307: noob mode

- Source: https://github.com/jepegit/issue-flow/issues/307
- Archived files: issue307_original.md, issue307_plan.md, issue307_status.md
- Summary: Added the `noob` knob (default off; first-time `--mode novice` seeds `noob = true`). When on, rendered stems get a footer that runs `issue-flow agent state --json` and prints `next_command` as Recommended plus a stem-specific `/iflow-*` list, without auto-dispatch. Docs distinguish `noob` from `novice`; this repo's `config.toml` was left off.

## Issue #306: pick issue then create epic then publish auto all

- Source: https://github.com/jepegit/issue-flow/issues/306
- Archived files: issue306_original.md, issue306_plan.md, issue306_status.md
- Summary: Shipped compose-only `/iflow-drive <N>`: draft epic, publish all stages, `/iflow-auto` each epoch, final review, local cleanup `-d` only, then `/iflow-status`. Skill/command templates, stem registration, off-path lists, abort tokens, and `drive-mode.md` landed. Version 0.5.4 → 0.5.5.

## Issue #303: Default-branch diverge: ff-only fails after unpushed home commits + a squash merge

- Source: https://github.com/jepegit/issue-flow/issues/303
- Archived files: issue303_original.md, issue303_plan.md, issue303_status.md
- Summary: Added `issue-flow agent default-sync --json` to classify unique default-branch commits without mutating. `worktree-add` still starts from `origin/<default>` when home is ahead; switchback attaches `default_sync` on ff-only refusal. Pick/issue/fix no longer require home FF; cleanup/close recover via an action table; epic/doctor/init must not leave unpushed commits on default. Design note `default-branch-diverge.md`. Version 0.5.4.

## Issue #298: Native Windows APPDATA tests (not a WSL bridge)

- Source: https://github.com/jepegit/issue-flow/issues/298
- Archived files: issue298_original.md, issue298_plan.md, issue298_status.md
- Summary: Added native win32 APPDATA / fallback / editor-global tests via monkeypatch (no `/mnt/c`). Linux/WSL still prefers XDG over APPDATA. Configuration and both design docs updated.

## Issue #297: Opt-in discover of .issueflows/ trees

- Source: https://github.com/jepegit/issue-flow/issues/297
- Archived files: issue297_original.md, issue297_plan.md, issue297_status.md
- Summary: `issue-flow register --discover [START]` walks for `.issueflows/` trees (default depth 4, no symlink follow), confirming unless `--yes`. Not hooked from init, `update --all`, or `workspace update`. Tests cover two scaffolds, a decoy, and the depth cap.

## Issue #296: Dedupe workspace update and the registry

- Source: https://github.com/jepegit/issue-flow/issues/296
- Archived files: issue296_original.md, issue296_plan.md, issue296_status.md
- Summary: `update --all --workspace` unions registry + nearest workspace members, unique by resolved path. Default `update --all` stays registry-only; `--workspace` without `--all` errors. `workspace update` skips duplicate resolved member paths.

## Issue #293: Materialize both stems into per-editor user-global skill dirs

- Source: https://github.com/jepegit/issue-flow/issues/293
- Archived files: issue293_original.md, issue293_plan.md, issue293_status.md
- Summary: `init` / `update` now write `caveman`, `grill-me`, and `gh-ci` into the selected editor's user-global skill dir while keeping the project copy. Stamps live under `$XDG_CONFIG_HOME/issue-flow/skill-stamps.json`; `--force` is `overwrite_foreign` on that tree. Per-editor paths: Cursor, Claude, Codex, and opencode as verified in #292.

## Issue #292: Confirm or skip opencode's user-global skill path

- Source: https://github.com/jepegit/issue-flow/issues/292
- Archived files: issue292_original.md, issue292_plan.md, issue292_status.md
- Summary: Doc-only verification that opencode's global write target is `~/.config/opencode/skills/` (2026-09-17 docs). Compat reads of `~/.claude/skills/` and `~/.agents/skills/` are not primary writes. Table row marked verified so Stage 3 materialize would not guess.

## Issue #288: Prevent HISTORY conflicts: defer_changelog (write on default after merge)

- Source: https://github.com/jepegit/issue-flow/issues/288
- Archived files: issue288_original.md, issue288_plan.md, issue288_status.md
- Summary: Shipped `defer_changelog` (project > user-global > env > default false) and `history.py` writers for append/promote/has-bullet/parse deferred. `issue-flow agent apply-changelog --issue N` writes on the default branch only. Close, history-update, cleanup, yolo, cycle, and rules were baked. Version 0.5.2 → 0.5.3.

## Issue #287: Registry of issue-flowed projects + update-all

- Source: https://github.com/jepegit/issue-flow/issues/287
- Archived files: issue287_original.md, issue287_plan.md, issue287_status.md
- Summary: Persist `registry.toml` next to user-global config. `init` and `register` add the current root; `unregister` removes it. `issue-flow update --all` walks the registry, skips missing and locked roots, forwards `--force` / `--editor`, and aggregates like `workspace update`. No workspace file required.

## Issue #286: Per-repo lock flag

- Source: https://github.com/jepegit/issue-flow/issues/286
- Archived files: issue286_original.md, issue286_plan.md, issue286_status.md
- Summary: Shipped `[issueflow] locked` (default false, project `config.toml` only). `config show|set` report it; `--global locked` is refused and user-global `locked` is ignored. `ISSUEFLOW_LOCKED` overrides for one process.

## Issue #285: User-global config file + resolve precedence

- Source: https://github.com/jepegit/issue-flow/issues/285
- Archived files: issue285_original.md, issue285_plan.md, issue285_status.md
- Summary: Implemented user-global `config.toml` (XDG / `%APPDATA%`) and preference-knob resolution project > user-global > env > default. `issue-flow config show|set --global` landed; `mode` is refused on `--global`. Missing user file keeps prior behaviour.

## Issue #282: Skill split — which packaged stems are global vs project-local

- Source: https://github.com/jepegit/issue-flow/issues/282
- Archived files: issue282_original.md, issue282_plan.md, issue282_status.md
- Summary: Doc-only classification of packaged stems as `global` | `local` | `both` in `global-vs-local-skills.md`. Lifecycle `iflow_*` stay local; `caveman` / `grill-me` / `gh-ci` are both. Cursor `~/.cursor/skills/` verified (also reads Claude's path); Claude/Codex recorded; opencode left unknown until #292.

## Issue #281: Design doc — user-global config, lock, registry, update-all

- Source: https://github.com/jepegit/issue-flow/issues/281
- Archived files: issue281_original.md, issue281_plan.md, issue281_status.md
- Summary: Wrote the design contract `user-global-config.md` covering path, precedence (project > user-global > env > default), project-only lock, registry, and `update --all` vs `workspace update`. Knobs table and `docs/configuration.md` gained pointers; Stage 2 specs in `epic269_plan.md` cite the doc. No `src/` behaviour in this issue.

## Issue #277: doctor: report unmanaged editor skills

- Source: https://github.com/jepegit/issue-flow/issues/277
- Archived files: issue277_original.md, issue277_plan.md, issue277_status.md
- Summary: Doctor now reports INFO `unmanaged_editor_skill` for extra skill directories that are not packaged stems. `--fix` does not delete them. Tests cover extras listed, packaged names omitted, and `--fix` leaving foreign folders. Documented in `dirty-issueflows.md` and `docs/cli.md`.

## Issue #276: update: warn or skip when a packaged skill path is not last render

- Source: https://github.com/jepegit/issue-flow/issues/276
- Archived files: issue276_original.md, issue276_plan.md, issue276_status.md
- Summary: `update` now uses a stamp store and skips foreign skill dirs (symlink, extras, stamp mismatch) instead of clobbering; `--force` overwrites without following symlink targets. Ours still refresh. Version 0.4.19 → 0.4.20.

## Issue #275: Learn from skillbook

- Source: https://github.com/jepegit/issue-flow/issues/275
- Archived files: issue275_original.md, issue275_plan.md, issue275_status.md
- Summary: Surveyed `kurochenko/skillbook` and recorded decisions in `skillbook-lessons.md` after a grill. Follow-up issues filed: #276 (clobber), #277 (unmanaged-skill scan); comment on #268. No product-code change in this issue.

## Issue #273: worktree tweak

- Source: https://github.com/jepegit/issue-flow/issues/273
- Archived files: issue273_original.md, issue273_plan.md, issue273_status.md
- Summary: Dropped the skill/command open-window option (`open-workspace` is print-only; CLI `--open` remains a manual hatch). Wired `auto_remove_worktree` (default true): close runs `worktree-remove` from home after PR open or yolo merge, skipping stay/draft/failed/`--auto`-queued merge/dirty trees. No branch delete. Version 0.4.18.

## Issue #271: Iterative fixes: docs-epic-howto

- Source: https://github.com/jepegit/issue-flow/issues/271
- Archived files: issue271_original.md, issue271_status.md
- Summary: `/iflow-fix` session expanding `docs/how-to/epics.md` (mental model, worked example, one-stage publish, revise-next-stage) and `docs/how-to/auto-mode.md` (epic-only framing). Same Q&A mirrored into `docs/issue-workflow.md` for `/iflow-epic` and `/iflow-auto`.

## Issue #265: Iterative fixes: howto-subchapters

- Source: https://github.com/jepegit/issue-flow/issues/265
- Archived files: issue265_original.md, issue265_status.md
- Summary: `/iflow-fix` session that made How-to nav use a bare `how-to/index.md` section index (dropped labeled Overview) so children stay labeled subchapters. `zensical build` stayed clean.

## Issue #262: Add task-oriented how-to guides to the docs site

- Source: https://github.com/jepegit/issue-flow/issues/262
- Archived files: issue262_original.md, issue262_plan.md, issue262_status.md
- Summary: Added `docs/how-to/` (index plus eight guides), nested How-to nav in `zensical.toml`, and links from Getting started and Home Recipes. Build and tests stayed green.

## Issue #260: Multi-PR HISTORY conflicts: pr-sync refresh + optional defer_changelog

- Source: https://github.com/jepegit/issue-flow/issues/260
- Archived files: issue260_original.md, issue260_plan.md, issue260_status.md
- Summary: Shipped Part A — `issue-flow agent pr-sync` (dry-run / push / fail-fast / worktrees), `/iflow-pr-sync` skill/commands, and design doc `pr-queue-sync.md`. Part B `defer_changelog` was deferred and landed later as #288.

## Issue #258: Iterative fixes: agent-name-issue-no-confirm

- Source: https://github.com/jepegit/issue-flow/issues/258
- Archived files: issue258_original.md, issue258_status.md
- Summary: `/iflow-fix` session adding `[issueflow].fix_auto_name` (default false; env `ISSUEFLOW_FIX_AUTO_NAME`) so the agent can invent a session title/slug without a separate naming confirm. Also landed `issue-flow config show|set|edit`. Version 0.4.13 → 0.4.14.
