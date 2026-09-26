# Drive mode

**Issue:** [#306](https://github.com/jepegit/issue-flow/issues/306)
**Status:** decided 2026-09-19.

## Context

Want one off-path command that takes an **existing** GitHub issue and
runs the whole large-change path: epic draft → publish every stage →
`/iflow-auto` each epoch → a final review that creates leftover
findings → local cleanup (`-d` only) → `/iflow-status`.

This is **compose-only**. It does not replace `/iflow-epic`,
`/iflow-auto`, `/iflow-cycle`, or `/iflow-yolo`.

## Decisions

### Surface

Off-path skill/command **`/iflow-drive <N>`** (chat: `iflow drive <N>`).

`<N>` is already on GitHub and becomes the epic anchor. Drive never
creates the anchor (`/iflow-issue epic` is the path when none exists).

### Confirm contract

One up-front confirm covers:

- draft-accept (`Status: confirmed` after draft, unless grill-me)
- publish-all stages (replaces per-stage publish confirms)
- auto-all (`/iflow-auto` overnight auth for each unfinished stage)
- final-review creates / reopens
- the **non-yolo lane** for `yolo: no` issues (policy `cycle_nonyolo`)
- local cleanup: `-d` on reachable **and** `-D` on squash-landed
  (`local only`, both A1 and A2, orchestrator token `drive`)

Do **not** re-ask those mid-run. Still honour:

- auto's **budget ask** (accept / grant N more loops / abort) — a
  planned pause, not a drive failure
- cycle / yolo **stop conditions** (`onfail:stop` floor: clean default)

### Carry-through (issue #386)

The first real drive run stopped at every seam a human would have
walked past: the plan's first `yolo: no` issue, a `HISTORY.md`-style
conflict in a design-guide table, a child branch stacked on a
squash-landed parent, a PR that had already merged, and a "never
force-push" rule read as covering issue branches. The decisions:

- **`yolo: no` is a lane, not a stop.** Cycle runs such issues through
  the same chain and safeguards and lands them per `cycle_nonyolo`
  (`merge` default — the judgment means "needs a plan on record", which
  the lane produces; `pr-only` opens the PR and continues; `stop`
  restores the old halt). Per-run token `nonyolo:<policy>` on drive /
  auto / cycle. The queue payload lists `nonyolo` so the confirm names
  them.
- **Bookkeeping conflicts resolve keep-both.** The `[Unreleased]`
  resolver generalises to additive bullets / table rows in
  `04-designs-and-guides/*.md` and `issue<N>_status.md` (any position;
  headings / prose still refuse). `sync-branch` picks a resolver per
  path and reports `resolvers`. Product code is never touched.
- **Stacked children skip the landed parent.** `sync-branch --base
  <ref>` (`git rebase --onto`), auto-detected when an ancestor branch
  is provably landed (merged PR / zero cherry-unique / touched files
  byte-identical upstream).
- **"Already merged" is success.** Close / yolo / cycle pull default
  and record `merged`.
- **Constraint scope.** "Never rebase / force-push / push" applies to
  the **default branch**. Issue branches are rewritten by sync-branch +
  `--force-with-lease` as normal.
- **Version drift is surfaced, not guessed.** `agent state` /
  `preflight` report `cli_version` / `skills_version` /
  `version_drift`; `/iflow` prints one warning and continues.
  (`issue_flow.__version__` now comes from package metadata — the
  hard-coded `0.4.2a4` was the root cause of every stale stamp.)

### Grill

`grill` / `grill-me` token **or** baked `grill_me_default` → run
grill-me on the epic goal before draft-accept. Otherwise auto-confirm
the draft under the drive confirm.

### Existing confirmed epic

If `epic<N>_plan.md` is already `Status: confirmed`, skip draft and
publish; jump to `/iflow-auto`.

### Publish and #303

`Published: #<M>` lines must land on a chore/issue branch or tiny PR —
never as unpushed commits on home default. Same rule as `/iflow-epic`
publish (issue #303).

### Auto each part

While `epic-status` has unfinished published stages, run `/iflow-auto
<N>` (forward `loops:<n>` and `nonyolo:<policy>`). Honour
`epoch_gated`. A `yolo: no` child is not a stop (see carry-through).
Append created / reopened numbers to `drive_status.md` `findings:`.

### Final review

When every published stage is `done` (or the user accepted a budget
ask): `/iflow-auto <N> review`. Create/reopen leftover findings using
the [advanced-auto-mode.md](./advanced-auto-mode.md) criteria table.
Do **not** start another epoch from drive.

### Cleanup (`-d` + `-D` under the drive confirm)

`/iflow-cleanup` with `local only` and the orchestrator token `drive`
(so A1 and A2 run without re-asking):

- switch / FF / fetch
- `worktree-remove` for `reachable` and `squash_landed`
- `git branch -d` on `reachable`
- `git branch -D` on `squash_landed`, and on `merged_pr_divergent`
  only when no unique commit is newer than the PR's `mergedAt`

Leave `unique_work` (and `skipped`) always. Print every `-D` tip SHA.
Never Phase B. Rationale: a drive that lands 5–15 squash PRs and then
leaves every branch behind for a manual `-D` pass is not hands-off;
the confirm names `-D` explicitly, so the human still authorized it.

### Abort tokens

Any user message that *is* (or starts with) `abort` / `stop` /
`cancel` / `halt` (case-insensitive, optional leading `/`) stops at
the **next stage or issue boundary**. Record `aborted` in
`drive_status.md`. Same floor as cycle `onfail:stop`.

### Durable state

`.issueflows/01-current-issues/drive_status.md` (name fixed here):

- anchor number
- checklist: `draft` / `publish` / `auto` / `final_review` / `cleanup`
  / `status`
- `findings:` (created / reopened numbers)
- last outcome: `pending` / `aborted` / `done`

Not an `issue<N>_*` group — folder sweeps leave it alone.

## Non-goals

- New CLI subcommand
- Forking yolo / cycle / auto / epic internals
- Auto-dispatch from `/iflow`
- Phase B (remote deletes / findings issue) from drive
- `-D` on `unique_work`, ever
- Creating the epic anchor

## Link

Auto: [advanced-auto-mode.md](./advanced-auto-mode.md).
Cleanup: [local-branch-cleanup.md](./local-branch-cleanup.md).
Default diverge: [default-branch-diverge.md](./default-branch-diverge.md).
