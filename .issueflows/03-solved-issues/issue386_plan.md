# Plan: #386 drive carries through under the overnight confirm

## Goal

Make `/iflow-drive` (and the `/iflow-auto` → `/iflow-cycle` chain it
composes) finish a real epic unattended: never stop on a `yolo: no` issue
it could have seen up front, resolve every *bookkeeping* conflict the
resolver can prove safe, understand stacked / squash-merged branches, and
stop contradicting `/iflow-close`. Surface skill-vs-CLI version drift —
and fix the bug that made every scaffolded skill claim `0.4.2a4`.

## Constraints

- Compose, do not fork: drive/auto/cycle still *call* yolo / plan / build /
  close / cleanup skills. New behaviour lives in those skills' text plus
  deterministic CLI helpers under `issue-flow agent`.
- Product-code conflicts still **stop**. The additive resolver only widens
  to files whose whole content is bookkeeping (see B).
- Never rewrite / force-push / push the **default** branch. Issue branches
  may be rebased and `--force-with-lease` pushed (close already does this).
- `git branch -D` only for `squash_landed` / `merged_pr_divergent` with a
  `MERGED` PR, only under an explicit confirm (drive confirm counts).
- Non-yolo lane still runs the full `capture → plan → build → close`
  chain with the **reasoning** profile; it removes prompts, not steps.
- Knob naming follows `skill-behaviour-knobs.md` (`cycle_*` value knobs).
- Docs / design guides updated; template + rendered-copy tests kept green.

### Prior art

- `agent.run_sync_branch` + `_resolve_sync_conflicts` (`agent.py`) and
  `history.resolve_changelog_conflict` (`history.py`) — the one-shape
  resolver to generalise. Rebase/merge plumbing in `gitutils`.
- `agent.run_local_branches` — `squash_landed` / `merged_pr_divergent`
  classification via `gitutils.cherry_unique_count`, `is_ancestor`,
  `gh_prs_by_head`. Reuse for stacked-parent detection and drive cleanup.
- `epicplan.IssueSpec.yolo` + `agent queue` payload already carries a
  per-issue `yolo` flag (`agent.py` ~L2608, L3143) — drive preflight and
  cycle lane selection read it; no new parsing.
- Knob wiring pattern: `cycle_onfail` (`modes.py` DEFAULT/ALLOWED/normalize/
  read, `config.py` resolve + context, `config_ops.py` spec, docs table
  test `test_doc_configuration.py`).
- `skill_ownership` reads `issue-flow-version` frontmatter; `templating.
  stamp_skill_version` writes it from `issue_flow.__version__`.
- Toolbox (`00-tools/`): nothing relevant. Graph absent in worktree.

## Approach

### A. Drive knows about `yolo: no` before it starts

1. **`agent epic-status` / `agent queue`** already expose `yolo` per
   issue. Add `nonyolo` list + count to the `queue --epic` payload summary
   so skills can quote it without iterating.
2. **Drive preflight (skill):** before the drive confirm, read the planned
   stages' `yolo:` flags. List non-yolo issues in the confirm, state which
   lane they take and the merge policy. `dry-run` prints the flag per
   queued issue.
3. **Non-yolo lane (cycle skill):** per issue, `yolo: yes` → yolo chain
   (unchanged). `yolo: no` → `capture → plan → build → close` with the
   reasoning profile, plan auto-accepted under the batch confirm, yolo's
   "not actually small" scope check **logged as advisory** in the status
   file (no abort). Merge policy from knob `cycle_nonyolo`:
   `merge` (same as yolo: `gh pr merge --squash`, retry rules), `pr-only`
   (open PR, leave merge, continue with the next issue stacked on the
   branch), `stop` (today's behaviour). Per-run token `nonyolo:<policy>`.
   Default **`merge`** (overnight = authorisation to land).
4. **Auto / drive skills:** forward the lane + policy; auto's overnight
   confirm and drive's confirm cover it. Cycle 6c no longer trips for a
   non-yolo-lane issue on the scope check alone.

### B. Resolver widens to additive bookkeeping

1. `history.py`: add `resolve_additive_conflict(text, *, in_flight_side,
   allow_tables)` — same keep-both rule (landed first, in-flight last,
   identical lines collapse) for conflict blocks whose sides are only list
   items / **table rows** (`|…|`) / blank / continuation lines, anywhere
   in the file. Headings, prose, code fences → refuse (so the duplicated
   `## Link` case stops and asks). `resolve_changelog_conflict` stays
   strict for `HISTORY.md`.
2. `agent._resolve_sync_conflicts`: classify each conflicted path:
   `HISTORY.md` → changelog resolver; anything under
   `.issueflows/04-designs-and-guides/` or matching
   `.issueflows/**/issue*_status.md` → additive resolver; else abort.
   Loop per conflicted commit as today. Payload: `resolved_paths`,
   `resolver` per path, `changelog_resolved` kept for back-compat.

### C. Stacked / squash-landed parents

1. `agent sync-branch --base <ref>`: rebase `--onto origin/<default>
   <ref>` so the parent's commits are dropped (child of a squash-merged
   PR). Refuse when `<ref>` is not an ancestor of HEAD.
2. **Auto-detect** when `--base` is absent: candidate = local branch (or
   `origin/*` ref) that is an ancestor of HEAD, not an ancestor of
   `origin/<default>`, and either has a `MERGED` PR for that head or
   `cherry_unique_count == 0`. Pick the nearest; report `base_detected` +
   `dropped_commits`. `git rebase` already drops single patch-identical
   commits; this covers the multi-commit squash case.
3. `gitutils.rebase_onto(cwd, ref, base=None)` gains the `--onto` form.
4. Skills (close / cycle / pr-sync): "already merged" from `gh pr merge`
   is **success** — check `gh pr view --json state` and continue.

### D. Constraint wording

Drive constraints: "Never rewrite, force-push or push the **default**
branch directly. Issue-branch rebase + `--force-with-lease` is owned by
`/iflow-close` and allowed." Same sentence in `drive-mode.md`. Auto /
cycle: under the overnight confirm they run `sync-branch` and retry the
merge for any resolver-supported conflict; stop only on resolver exit 1.

### E. Drive cleanup may `-D`

Drive step 10: `/iflow-cleanup local only` **with** Phase A2 for
`squash_landed` (and `merged_pr_divergent` with a `MERGED` PR whose unique
commits are all older than `mergedAt`), covered by the drive confirm.
`unique_work` never. Cleanup skill: token `landed` (or the drive caller)
= A2 pre-confirmed. Report tips so the SHAs stay in the transcript.

### F. Version drift + small things

1. `issue_flow.__version__` → `importlib.metadata.version("issue-flow")`
   with fallback. Skill stamps become correct (bug behind "0.4.2a4").
2. `agent state` payload: `cli_version`, `skills_version` (read from the
   rendered `iflow/SKILL.md` frontmatter in the agent dir), `version_drift`
   bool + note "run `issue-flow update`". `/iflow` dispatcher prints the
   warning when set. `preflight` mirrors the three fields.
3. `_body.md.j2` graph section: "if `graphify-out/graph.json` exists"
   (not just the folder).
4. Drive `dry-run`: yolo flags per queued issue (from A2).

## Files to touch

- `src/issue_flow/__init__.py` — metadata-derived `__version__`.
- `src/issue_flow/history.py` — `resolve_additive_conflict`, table-row
  predicate, shared `_merge_sides`.
- `src/issue_flow/gitutils.py` — `rebase_onto(..., base=)`,
  `local_branches_ancestor_of_head` helper (or reuse `is_ancestor`).
- `src/issue_flow/agent.py` — `run_sync_branch` (`--base`, auto-detect,
  per-path resolver), `run_state` / `run_preflight` version fields,
  `queue --epic` nonyolo summary.
- `src/issue_flow/cli.py` — `sync-branch --base`, docstrings.
- `src/issue_flow/modes.py`, `config.py`, `config_ops.py`,
  `templating.py` context — knob `cycle_nonyolo`
  (`merge|pr-only|stop`, default `merge`, env
  `ISSUEFLOW_CYCLE_NONYOLO`).
- Templates: `skills/iflow_drive`, `iflow_auto`, `iflow_cycle`,
  `iflow_close`, `iflow_cleanup`, `iflow_iflow`, `iflow_pr_sync`,
  `iflow_history_update` (resolver scope), matching `commands/*.md.j2`,
  `rules/_body.md.j2`, `docs/issue-workflow.md.j2`.
- Docs: `docs/cli.md` (sync-branch flags, state fields),
  `docs/configuration.md` (knob row), `docs/how-to/drive.md`,
  `docs/how-to/pr-sync.md`, `docs/issue-workflow.md` (re-render).
- Design guides: `drive-mode.md` (lane, cleanup, constraint),
  `advanced-auto-mode.md` (stop conditions), `pr-queue-sync.md`
  (resolver scope + stacked), `skill-behaviour-knobs.md` (knob row),
  `test-registry.md`.
- Tests: `tests/test_history.py` (additive resolver: bullets, table rows,
  refuse heading/prose), `tests/test_agent_sync_branch.py` (designs +
  status resolve, `--base`, auto-detect stacked parent, product conflict
  still aborts), `tests/test_cli.py` (state/preflight version fields,
  `sync-branch --base`), `tests/test_config.py` + `test_doc_configuration`
  (knob), `tests/test_templating.py` (drive/auto/cycle/cleanup wording,
  version stamp equals metadata), `tests/test_update.py` if it pins the
  stamp.

## Test strategy

`uv run pytest` (full), `uv run ruff check --fix src/ tests/` +
`uv run ruff format`. New unit tests as listed; git-backed tests build a
temp repo with an origin, a squash-merged parent branch and a stacked
child to prove `--base` / auto-detect. Live check: render skills into a
temp project and grep the drive confirm / constraint wording; run
`issue-flow agent state --json` in this worktree and see
`version_drift: true` until `issue-flow update`.

## Open questions

1. `cycle_nonyolo` default **`merge`** (overnight = land) vs `pr-only`
   (safer, human merges later). Plan assumes `merge`.
2. Auto-detected stacked base: proceed silently, or only report and
   require `--base`? Plan: proceed, but record `base_detected` and abort
   if the dropped commits touch paths the remaining commits do not
   (sanity guard).
3. Drive cleanup `-D` on `merged_pr_divergent`: include (with the
   "no commit newer than mergedAt" guard) or `squash_landed` only? Plan
   includes both under that guard.
