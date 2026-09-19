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
- reachable-only local cleanup (`local only`, no Phase A2)

Do **not** re-ask those mid-run. Still honour:

- auto's **budget ask** (accept / grant N more loops / abort) — a
  planned pause, not a drive failure
- cycle / yolo **stop conditions** (`onfail:stop` floor: clean default)

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
<N>` (forward `loops:<n>`). Honour `epoch_gated`. Append created /
reopened numbers to `drive_status.md` `findings:`.

### Final review

When every published stage is `done` (or the user accepted a budget
ask): `/iflow-auto <N> review`. Create/reopen leftover findings using
the [advanced-auto-mode.md](./advanced-auto-mode.md) criteria table.
Do **not** start another epoch from drive.

### Cleanup (`-d` only)

`/iflow-cleanup` with `local only` **and skip Phase A2**:

- switch / FF / fetch
- `worktree-remove` for `reachable` only
- `git branch -d` on `reachable` only

Leave `squash_landed`, `merged_pr_divergent`, `unique_work`. Never
`-D`. Never Phase B.

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
- Phase B / `git branch -D` from drive
- Creating the epic anchor

## Link

Auto: [advanced-auto-mode.md](./advanced-auto-mode.md).
Cleanup: [local-branch-cleanup.md](./local-branch-cleanup.md).
Default diverge: [default-branch-diverge.md](./default-branch-diverge.md).
