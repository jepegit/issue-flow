# Raw session log for #363 (issue #328), recorded as it happened

Editor: Claude Code. Repo: jepegit/issue-flow. Date: 2026-09-24.

## 1. User: `iflow pick`

Agent actions (tools):
- `git fetch --prune`; `issue-flow agent preflight --json` → on `main`, not clean, issueflows-only dirt: auto_status.md, drive_status.md, 2 cycle logs
- no parked groups in 02-partly-solved-issues/; epic #341 next_candidates: []
- `gh issue list --state open` → 15 open; dropped #260 (solved locally), #341 (epic anchor), #267 (audit chore), #363 (depends on this session)

Agent reply (shortlist + gate), as printed:

> Preflight: on `main`, up to date with origin. The working tree has uncommitted **tracking files only**: `auto_status.md`, `drive_status.md` and two cycle logs from the #341 drive. No parked work, no open epic candidates.
>
> Open issues, ranked (already-tracked ones left out):
>
> | # | Issue | Labels / milestone | Why it ranks here |
> |---|---|---|---|
> | 1 | #328 location of worktrees | — | Close to recent work (worktree-first start, workspaces) |
> | 2 | #248 option for not stopping in a cycle | v.0.5.0 | Cycle behaviour; milestone |
> | 3 | #308 publish on success | — | Release flow |
> | 4 | #268 Improve skills | — | Broad; may need a split |
> | 5 | #100 Custom templates — let users override Jinja2 scaffolds | v.0.5.0 | Milestone |
>
> Which one? Reply with the issue number (or "1").
>
> Also: the tracking files on `main` must not end up on the new branch. The new issue worktree starts from `origin/main`, so they stay behind on `main`. Either:
> **(a)** commit them on a small chore branch + PR first (recommended; keeps `main` clean), or
> **(b)** leave them uncommitted on `main` for now.

## 2. User: `1, a`

Agent actions:
- (a) committed the 4 tracking files + a plan outcome note on `chore/epic341-drive2-record` → PR #374; back on `main`, tree clean.
- `issue-flow agent default-sync --json` → `even`
- `issue-flow agent worktree-add 328 --slug worktree-location --json` →
  ```json
  {"path": ".../issue-flow-workspace/issue-flow-328", "branch": "328-worktree-location", "home_branch": "main", "created": true, "error": null}
  ```
  (note: the worktree lands next to the repo, `../issue-flow-328`, i.e. the *current* behaviour #328 is about)
- `issue-flow agent open-workspace ../issue-flow-328 --json` → prints the path (print-only)
- `issue-flow agent capture 328` → wrote `.issueflows/01-current-issues/issue328_original.md`
- sweep: nothing to sweep
- auto_plan = true → chains into `iflow plan`

## 3. `iflow plan` (chained by auto_plan)

Agent actions (read-only research):
- read `issue328_original.md`; skimmed `04-designs-and-guides/` (separate-workspaces.md, multi-repo-workspaces.md)
- prior art: `gitutils.worktree_path_for_issue` (single path source), `project.find_workspace_file` (workspace detection), `Settings.resolve_worktree_first` (knob pattern); 4 template mentions of `<repo>-<N>`
- wrote `.issueflows/01-current-issues/issue328_plan.md` (Goal / Constraints + Prior art / Approach / Files to touch / Test strategy / Open questions — 4 open questions with recommendations)
- STOP: asked for Accept / Revise / Abort (no code written)

(plan file content captured separately at merge time from 03-solved-issues/issue328_plan.md)

## 4. User: `Accept`

auto_build = true → chains into `iflow build`.

## 5. `iflow build`

- seeded `issue328_status.md` (- [ ] Done)
- code: two settings (`config_ops`, `modes`, `config`), `gitutils.resolve_worktree_location` + `WorktreeLocation`, `worktree-add` payload gains `location` / `location_note`, `worktree-remove <N>` uses the same resolver
- first full test run → 1 failure, from the docs guard added in #359:
  ```
  FAILED tests/test_doc_configuration.py::test_all_settings_table_lists_every_config_key_once
  AssertionError: missing: ['worktrees_dir', 'worktrees_in_workspace'], unknown: []
  ```
  (the new settings were not documented yet — exactly what that test is for)
- docs: `configuration.md` (2 rows + a Common changes row), `how-to/worktrees.md` ("Where the worktree goes"), 3 templates (re-rendered), design note `separate-workspaces.md`
- tests: `tests/test_worktree_location.py` (10: one per table row + fallbacks + `~` + CLI add/remove + project-vs-user override)
- real run in a throwaway HOME:
  ```text
  $ issue-flow config set --global worktrees_dir '~/worktrees'
  $ issue-flow agent worktree-add 6 --slug demo -C projects/demo
  Created: <tmp>/home/worktrees/demo-6  (worktrees_dir)
  Branch: 6-demo
  Home: <tmp>/projects/demo (main)

  # after deleting ~/worktrees:
  $ issue-flow agent worktree-add 7 --slug demo -C projects/demo
  Created: <tmp>/projects/demo-7  (fallback)
  note  worktrees_dir '<tmp>/home/worktrees' does not exist; using the repo's parent folder
  ```
- full suite: 882 passed; link check: 0 errors
- status file updated (still `- [ ] Done`); auto_close = false → handed off: "run `iflow close`"

## 6. User: `iflow close`

Agent actions:
- sanity: `pytest -m essential` → 18 passed; full `pytest` → 882 passed; ruff clean; no unrelated changes
- essential review: 3 new resolver tests marked essential (done during build; registry updated)
- no bump requested (confirm_version_bump = false) → no version change
- HISTORY.md: appended an `[Unreleased]` bullet without asking (confirm_changelog_update = false)
- status → `- [x] Done`; moved `issue328_*` to `03-solved-issues/`
- commit `feat: choose where issue worktrees go (worktrees_dir)`; `issue-flow agent sync-branch` → already up to date with origin/main; push
- `gh pr list --head 328-worktree-location` → none → `gh pr create` → PR #375 (`Closes #328`)
- checks snapshot: 5 checks pending
- switchback: in a linked worktree → pulled `main` from home instead
- `issue-flow agent worktree-remove 328` → removed (clean tree, auto_remove_worktree = true); branch kept
- NOT merged (no `yolo` token) → reminder: merge on GitHub, then `iflow cleanup`
- CI on PR #375: all 5 checks pass (test 3.12/3.13/3.14, docs-links, approval)

## 7. User: `iflow cleanup` (first try)

Agent actions:
- `gh pr view 375` → OPEN, not merged (PR #374 also open)
- on `main`, even with origin; no linked worktrees
- `issue-flow agent local-branches` → 8 squash_landed (earlier work), `328-worktree-location` and `chore/epic341-drive2-record` = unique_work (their PRs are not merged yet)
- STOP Phase A: "PR #375 is not merged yet — merge it on GitHub (or tell me to), then run `iflow cleanup` again." Nothing deleted.

## 8. User: "merged 375 now" (cleanup, second try)

Agent actions:
- `gh pr view 375` → MERGED (squash commit 097a7b2); `main` is 1 behind origin
- `issue-flow agent local-branches` → reachable: none; squash_landed: `328-worktree-location` 54da663 (#375) + 8 older; unique_work: `chore/epic341-drive2-record` (PR #374 still open → never offered)
- Phase A1 confirm (pull --ff-only, fetch --prune; no -d candidates) and a SEPARATE Phase A2 confirm (-D on the 9 squash-landed branches, tip SHAs listed)
- User answered: Phase A1 = Yes; Phase A2 = Yes, delete all 9
- `git pull --ff-only` → main at 097a7b2 feat: choose where issue worktrees go (worktrees_dir) (#375); `git fetch --prune`
- deleted (name, tip, flag):
  328-worktree-location 54da663 -D
  358-command-reference 88fddba -D
  358-link-texts 02178cf -D
  359-config-page a400854 -D
  360-troubleshooting 7d755fc -D
  361-diagrams f02df06 -D
  362-missing-howtos d1de16c -D
  364-queue-closed-deps 38cf334 -D
  chore/epic341-stages-3-4 d2fc88f -D
- kept: chore/epic341-drive2-record (PR #374 open)
- folder sweep: nothing to move (issue328_* already in 03-solved-issues by close)
- epic stage gate: #328 is not in any epic plan → nothing to offer
