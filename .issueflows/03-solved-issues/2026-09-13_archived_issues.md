# Archived issues — 2026-09-13

Pre-archive git ref: `57dd74cff883e64047aa676b017db08ebb123b85`
Recover any archived file with `git show <sha>:<path>` (or browse `git log -- <path>`).

## Issue #12: Create linked (sub) issues for over-ambitious issues

- Source: https://github.com/jepegit/issue-flow/issues/12
- Archived files: issue12_original.md, issue12_plan.md, issue12_status.md
- Summary: Introduced `/iflow-split` to cut one oversized issue into 2–5 flat GitHub sub-issues behind a consolidated confirm, distinct from staged `/iflow-epic` work. Design doc `linked-sub-issues.md`, CLI/templating support, and tests landed; parent stays open as tracker.

## Issue #23: conversion for teams using multiple coding environments

- Source: https://github.com/jepegit/issue-flow/issues/23
- Archived files: issue23_original.md, issue23_plan.md, issue23_status.md
- Summary: Phase 1 shipped a canonical `.issueflows/agent/` store plus `issue-flow convert` so multi-editor teams share one committed skill layout. Docs and tests covered conversion; git hooks deferred. Landed in PR #161.

## Issue #47: how to handle dirty issueflows directories

- Source: https://github.com/jepegit/issue-flow/issues/47
- Archived files: issue47_original.md, issue47_plan.md, issue47_status.md
- Summary: Defined dirty `.issueflows/` conditions and shipped `issue-flow doctor` / `agent audit` / `agent repair` plus `/iflow-doctor`. Safe repairs gated on confirm; design doc `dirty-issueflows.md`. PR #165.

## Issue #99: Create pull request early

- Source: https://github.com/jepegit/issue-flow/issues/99
- Archived files: issue99_original.md, issue99_plan.md, issue99_status.md
- Summary: Added optional early draft PR during `/iflow-build` via `early_pr` config and trailing `early`/`noearly` overrides. Close still owns HISTORY timing; design doc `early-pr.md`. PR #190.

## Issue #102: GitHub Actions workflow — sync .issueflows/ state to GitHub labels/milestones

- Source: https://github.com/jepegit/issue-flow/issues/102
- Archived files: issue102_original.md, issue102_plan.md, issue102_status.md
- Summary: Built a sync engine mapping local tracking folders to GitHub status labels/milestones, with CLI and workflow hooks. Pure collect/map/apply layer in `sync.py` plus tests. PR #160.

## Issue #141: Cycling mode, stage 1: /iflow-cycle skill - sequential hands-off issue loop

- Source: https://github.com/jepegit/issue-flow/issues/141
- Archived files: issue141_original.md, issue141_plan.md, issue141_status.md
- Summary: Scaffolded `/iflow-cycle` as the batch yolo path: resolve a queue, one up-front confirm, then sequential hands-off closes with strict stop-on-fail. Later stages (#142/#143) completed resumability and optional parallel notes.

## Issue #142: Cycling mode, stage 2: cycle state file - resumability and failure policy

- Source: https://github.com/jepegit/issue-flow/issues/142
- Archived files: issue142_original.md, issue142_status.md
- Summary: Added `cycle_status.md` resumability and failure policy to the cycle skill, with `run_status` reporting `cycle_active`. Status/skill contract tests and HISTORY updates completed the stage.

## Issue #143: Cycling mode, stage 3: parallel dispatch for independent issues (experimental)

- Source: https://github.com/jepegit/issue-flow/issues/143
- Archived files: issue143_original.md, issue143_status.md
- Summary: Documented experimental opt-in `parallel:<n>` for independent cycle items only, with design record `parallel-cycle.md`. Skill/command and contract tests updated; sequential path remained the default.

## Issue #151: add a logo

- Source: https://github.com/jepegit/issue-flow/issues/151
- Archived files: issue151_original.md, issue151_plan.md, issue151_status.md
- Summary: Wired the docs theme logo to `docs/static/images/LOGO_01.png` and verified a successful Zensical build. Optional hero/favicon/rename work was intentionally skipped.

## Issue #153: possible misplacement of mode information

- Source: https://github.com/jepegit/issue-flow/issues/153
- Archived files: issue153_original.md, issue153_plan.md, issue153_status.md
- Summary: Removed duplicated mode/config user content from `docs/developing.md` so configuration docs stay the single source. Docs-only cleanup; tests and site build stayed green.

## Issue #158: update all issue flows in a workspace

- Source: https://github.com/jepegit/issue-flow/issues/158
- Archived files: issue158_original.md, issue158_plan.md, issue158_status.md
- Summary: Shipped `issue-flow workspace update` to refresh every scaffolded member from `issueflow-workspace.toml`, with JSON mode and partial-failure continue. Documented in multi-repo guide; PR #159.

## Issue #162: Docs check

- Source: https://github.com/jepegit/issue-flow/issues/162
- Archived files: issue162_original.md, issue162_plan.md, issue162_status.md
- Summary: Docs polish: better logo/favicon, dropped Safari-breaking instant navigation, and mobile overflow CSS. CLI synopsis wrapping fixed; site build verified.

## Issue #163: How to handle branches on GitHub

- Source: https://github.com/jepegit/issue-flow/issues/163
- Archived files: issue163_original.md, issue163_plan.md, issue163_status.md
- Summary: Extended `/iflow-cleanup` with an optional GitHub remote-branch audit (`include github`) behind further confirms, plus `issue-flow agent branches`. Design doc `github-branch-audit.md`; local Phase A unchanged.

## Issue #166: Issueflow sync dogfood workflow fails

- Source: https://github.com/jepegit/issue-flow/issues/166
- Archived files: issue166_original.md, issue166_plan.md, issue166_status.md
- Summary: Fixed sync dogfood failures by auto-creating missing managed status labels (`ensure_managed_labels` / `bootstrap_labels`). Tests and README updated; PR #167.

## Issue #168: fix GitHub Linguist skew

- Source: https://github.com/jepegit/issue-flow/issues/168
- Archived files: issue168_original.md, issue168_plan.md, issue168_status.md
- Summary: Added opt-in `linguist_attributes` so scaffolded paths can be marked for GitHub Linguist without skewing the language bar. Config/docs/tests and dogfood attributes enabled in this repo.

## Issue #171: Timing of updating changelog

- Source: https://github.com/jepegit/issue-flow/issues/171
- Archived files: issue171_original.md, issue171_plan.md, issue171_status.md
- Summary: Hardened HISTORY timing: changelog belongs in the close PR commit; no post-merge offers; declining changelog blocks continuing close. Design note `changelog-timing.md`.

## Issue #172: List and watch GitHub

- Source: https://github.com/jepegit/issue-flow/issues/172
- Archived files: issue172_original.md, issue172_plan.md, issue172_status.md
- Summary: Close/yolo paths now list existing PRs before create and snapshot `gh pr checks` afterward. Design doc `gh-list-and-watch.md`; avoids duplicate PRs and clarifies CI state.

## Issue #174: skill for reviewing and labelling issues

- Source: https://github.com/jepegit/issue-flow/issues/174
- Archived files: issue174_original.md, issue174_plan.md, issue174_status.md
- Summary: Added off-path `/iflow-review` (v1: apply configured yolo label) with consolidated confirm before label create/apply. CLI helpers and design doc `issue-review-labelling.md`; PR #177.

## Issue #175: auto process all yolo issues

- Source: https://github.com/jepegit/issue-flow/issues/175
- Archived files: issue175_original.md, issue175_plan.md, issue175_status.md
- Summary: Documented and aliased `/iflow-cycle yolo` → `label:<yolo_label>` with conflict stance for sequential merges. Review/workflow cross-links updated; PR #178.

## Issue #179: Review docs

- Source: https://github.com/jepegit/issue-flow/issues/179
- Archived files: issue179_original.md, issue179_plan.md, issue179_status.md
- Summary: Expanded workflow docs for epic/cycle/review with examples and fixed Agent Skills table rows. Version bump to 0.4.5; PR #180.

## Issue #181: create non-epic issue

- Source: https://github.com/jepegit/issue-flow/issues/181
- Archived files: issue181_original.md, issue181_plan.md, issue181_status.md
- Summary: Shipped `/iflow-issue` to create one well-specified normal GitHub issue then optionally capture into the lifecycle. Fills the gap between fix sessions and epics; design note `create-non-epic-issue.md`.

## Issue #182: More config settings

- Source: https://github.com/jepegit/issue-flow/issues/182
- Archived files: issue182_original.md, issue182_plan.md, issue182_status.md
- Summary: Added skill-behaviour knobs (`auto_switchback`, `auto_close`, confirm toggles, etc.) baked into templates on update. Design note `skill-behaviour-knobs.md`.

## Issue #183: renaming from start to build

- Source: https://github.com/jepegit/issue-flow/issues/183
- Archived files: issue183_original.md, issue183_plan.md, issue183_status.md
- Summary: Hard-renamed `/iflow-start` → `/iflow-build` across templates, registries, docs, and retirement aliases. Design note recorded the cut; tests updated.

## Issue #191: Design doc — advanced auto mode contract

- Source: https://github.com/jepegit/issue-flow/issues/191
- Archived files: issue191_original.md, issue191_plan.md, issue191_status.md
- Summary: Wrote durable `advanced-auto-mode.md` (epochs, overnight confirm, loop budget, auto_status, model hints). Docs-only contract issue with no code changes.

## Issue #192: Config knobs for adversarial loop budget

- Source: https://github.com/jepegit/issue-flow/issues/192
- Archived files: issue192_original.md, issue192_plan.md, issue192_status.md
- Summary: Wired `auto_adversarial_loops` (default 2) through config/env/templates and workflow bake-in. Foundation for `/iflow-auto` loop control.

## Issue #193: Epic plan markers — Stage Goal + issue Goal/Model

- Source: https://github.com/jepegit/issue-flow/issues/193
- Archived files: issue193_original.md, issue193_plan.md, issue193_status.md
- Summary: Extended epic plan parsing/docs for Stage Goal and per-issue Goal/Model markers, including epic-status JSON fields. Skill/command updated.

## Issue #194: /iflow-auto orchestrator skill (skeleton)

- Source: https://github.com/jepegit/issue-flow/issues/194
- Archived files: issue194_original.md, issue194_plan.md, issue194_status.md
- Summary: Registered off-path `/iflow-auto` skeleton: confirm epic, select stage, overnight confirm, cycle, adversarial stub. Docs/rules listed it off-path.

## Issue #195: Stage 1 tests and HISTORY

- Source: https://github.com/jepegit/issue-flow/issues/195
- Archived files: issue195_original.md, issue195_plan.md, issue195_status.md
- Summary: Closed Stage 1 gaps: init scaffolds `/iflow-auto`, profile defaults, env override tests, and configuration docs for `auto_adversarial_loops`.

## Issue #202: Adversarial review skill / `/iflow-auto review`

- Source: https://github.com/jepegit/issue-flow/issues/202
- Archived files: issue202_original.md, issue202_plan.md, issue202_status.md
- Summary: Replaced the adversarial stub with a real `review` procedure and criteria table in the design doc. Skill/command/docs/tests updated.

## Issue #203: Wire loop budget + ask UX into `/iflow-auto`

- Source: https://github.com/jepegit/issue-flow/issues/203
- Archived files: issue203_original.md, issue203_plan.md, issue203_status.md
- Summary: Added post-review loop control: increment, re-queue, or stop-and-ask when budget exhausted. Design doc manual scenario covered.

## Issue #204: Gate next epoch on clear queue

- Source: https://github.com/jepegit/issue-flow/issues/204
- Archived files: issue204_original.md, issue204_plan.md, issue204_status.md
- Summary: Gated advancing to stage k+1 on a clear queue (`epoch_gated` / continue / `complete`). Completes the auto-mode stage-advance contract.

## Issue #210: Iflow in epics

- Source: https://github.com/jepegit/issue-flow/issues/210
- Archived files: issue210_original.md, issue210_plan.md, issue210_status.md
- Summary: `/iflow` with no focus now surfaces active-epic `next_candidates` and recommends `/iflow-pick` instead of a blind capture. Design note `iflow-epic-awareness.md`; PR #235.

## Issue #211: option C problem

- Source: https://github.com/jepegit/issue-flow/issues/211
- Archived files: issue211_original.md, issue211_plan.md, issue211_status.md
- Summary: Fixed Typer option/argument collision by converting agent subcommands to a shared project-dir Option (e.g. `agent sweep -C`). Version 0.4.7; PR #212.

## Issue #213: option for using essential tests

- Source: https://github.com/jepegit/issue-flow/issues/213
- Archived files: issue213_original.md, issue213_plan.md, issue213_status.md
- Summary: Shipped essential-tests contract (`essential_tests`, markers, runner knobs) with close/build/doctor hooks. Design doc `essential-tests.md`; PR #226.

## Issue #214: always run graphify before planning

- Source: https://github.com/jepegit/issue-flow/issues/214
- Archived files: issue214_original.md, issue214_plan.md, issue214_status.md
- Summary: Added opt-in `auto_graphify_on_plan` (default false) so `/iflow-plan` can refresh the knowledge graph first. Config/docs/tests; PR #215.

## Issue #216: possible bug in gitutils

- Source: https://github.com/jepegit/issue-flow/issues/216
- Archived files: issue216_original.md, issue216_plan.md, issue216_status.md
- Summary: Fixed Windows `UnicodeDecodeError` / None-stdout crashes in gitutils `gh` subprocess handling (UTF-8 decode + safe stdout). PR #217.

## Issue #218: doctor leftovers

- Source: https://github.com/jepegit/issue-flow/issues/218
- Archived files: issue218_original.md, issue218_plan.md, issue218_status.md
- Summary: Taught doctor/close paths to treat issueflows-only dirty trees as non-blocking when appropriate (`issueflows_only_dirty`). PR #222.

## Issue #219: just build the thing when the plan is accepted

- Source: https://github.com/jepegit/issue-flow/issues/219
- Archived files: issue219_original.md, issue219_plan.md, issue219_status.md
- Summary: Added `auto_plan` / `auto_build` knobs (default true) so pick→plan→build can chain without extra prompts. Config/docs/tests; PR #223.

## Issue #220: utilizing gh for finding out when CI is green

- Source: https://github.com/jepegit/issue-flow/issues/220
- Archived files: issue220_original.md, issue220_plan.md, issue220_status.md
- Summary: Added model-invoked `gh-ci` skill cheatsheet (`gh pr checks` / watch with minute budget, run-list fallback). Close owns merge; skill is shared CI wait guidance. PR #225.

## Issue #224: Release

- Source: https://github.com/jepegit/issue-flow/issues/224
- Archived files: issue224_original.md, issue224_plan.md, issue224_status.md
- Summary: Refreshed the release playbook in developing.md, backfilled/promoted HISTORY, and bumped to 0.4.9 for `gh release create`.

## Issue #228: Allow picking based on label

- Source: https://github.com/jepegit/issue-flow/issues/228
- Archived files: issue228_original.md, issue228_plan.md, issue228_status.md
- Summary: `/iflow-pick` gained hard filter `label:<L>` for open GitHub issues. Documented vs cycle queue semantics in `label-driven-flows.md`.

## Issue #231: Add badges to readme

- Source: https://github.com/jepegit/issue-flow/issues/231
- Archived files: issue231_original.md, issue231_plan.md, issue231_status.md
- Summary: Added README badge row for PyPI, Read the Docs, and Pepy downloads under the H1. Small docs-facing yolo close.

## Issue #233: cleanup configurable

- Source: https://github.com/jepegit/issue-flow/issues/233
- Archived files: issue233_original.md, issue233_plan.md, issue233_status.md
- Summary: Clarified `remind_cleanup` as soft reminders only (never auto-run), and baked Phase B GitHub-audit defaults/opt-outs into cleanup. PR #234.

## Issue #240: Changelog conflicts

- Source: https://github.com/jepegit/issue-flow/issues/240
- Archived files: issue240_original.md, issue240_plan.md, issue240_status.md
- Summary: Added pure HISTORY conflict resolver in `history.py` for Keep-a-Changelog Unreleased merges, with refusal cases unit-tested. Design doc `changelog-conflicts.md`.

## Issue #241: rename iflow init to something else and use iflow init only for issuflow initialisation

- Source: https://github.com/jepegit/issue-flow/issues/241
- Archived files: issue241_original.md, issue241_plan.md, issue241_status.md
- Summary: Renamed issue-capture `/iflow-init` → `/iflow-capture`; reserved `/iflow-init` for harness cold-start. Stage ids and design doc `iflow-init-vs-capture.md`.

## Issue #243: `/iflow-cleanup` cannot prune squash-merged branches (`-d` vs `git cherry`)

- Source: https://github.com/jepegit/issue-flow/issues/243
- Archived files: issue243_original.md, issue243_plan.md, issue243_status.md
- Summary: Fixed squash-merge cleanup: classify reachable locals for `-d`, and offer `-D` only behind a second confirm with tip SHAs. Design doc `local-branch-cleanup.md`.

## Issue #246: set up project for novice and new users

- Source: https://github.com/jepegit/issue-flow/issues/246
- Archived files: issue246_original.md, issue246_plan.md, issue246_status.md
- Summary: Shipped `setup-status` facts plus `/iflow-setup` to walk git/gh/Python blockers one confirm at a time for new or existing projects.

## Issue #249: use parts of pstack

- Source: https://github.com/jepegit/issue-flow/issues/249
- Archived files: issue249_original.md, issue249_plan.md, issue249_status.md
- Summary: Curated optional pstack-derived skills (unslop, tdd, blast-radius, etc.) into the scaffold. Impl landed via #250; HISTORY bullet closed the tracking gap.

## Issue #251: Support no-PR / ops work (e.g. staging → production)

- Source: https://github.com/jepegit/issue-flow/issues/251
- Archived files: issue251_original.md, issue251_plan.md, issue251_status.md
- Summary: Added `/iflow-ops` and close `ops`/`nopr` path for no-PR work; ops label beats yolo on pick. Design doc `ops-no-pr.md`; version 0.4.11.

## Issue #253: Run parallel / multi-repo agent work in separate Cursor workspaces

- Source: https://github.com/jepegit/issue-flow/issues/253
- Archived files: issue253_original.md, issue253_plan.md, issue253_status.md
- Summary: Documented coordinator/worker separate windows and added `open-workspace` CLI hooks for cycle/parallel multi-repo. Design doc `separate-workspaces.md`; 0.4.12.

## Issue #255: Worktree + separate window on pick/issue start (keep home on default)

- Source: https://github.com/jepegit/issue-flow/issues/255
- Archived files: issue255_original.md, issue255_plan.md, issue255_status.md
- Summary: Added `agent worktree-add/list/remove` so pick/issue can open work in a sibling worktree while home stays on default. Extends separate-workspaces design; 0.4.13.
