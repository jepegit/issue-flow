# Plan: #306 pick → epic → publish → auto-all

## Goal

Add one off-path orchestrator that takes an existing GitHub issue `<N>`
and runs: draft epic (auto-accept unless grill-me) → publish every
stage → `/iflow-auto` each epoch → final review (create leftover
findings) → local cleanup **`-d` only** → `/iflow-status`. User
`abort` / `stop` / `cancel` / `halt` stops the run.

## Constraints

- Compose existing skills. Do **not** fork yolo/cycle/auto internals.
- Off-path; `/iflow` never auto-dispatches it.
- One up-front confirm covers draft-accept + publish-all + auto-all +
  final-review creates + reachable-only cleanup. Do not re-ask those
  confirms mid-run (auto’s budget ask and cycle/yolo *stop conditions*
  still apply).
- Never rebase / force-push / push default. Cleanup never `-D`, never
  Phase B.
- Templates are source of truth.
- User already chose **whole issue** at pick (not split).

### Prior art

- `/iflow-epic <N>` — draft `epic<N>_plan.md` from an existing anchor;
  `publish [stage <k>]` creates issues. Drive calls both.
- `/iflow-issue epic` — **only** when no anchor exists. Drive requires
  `<N>` already on GitHub.
- `/iflow-auto <N>` + `advanced-auto-mode.md` — stage cycle, inter-epoch
  adversarial review, `auto_status.md`, loop budget. Drive loops this
  until `epic-status` says all published stages done (or stop/abort).
- `/iflow-cycle` — per-stage execution; overnight confirm is satisfied
  by drive’s confirm.
- `/iflow-cleanup` `local only` — skips Phase B. **New:** drive also
  skips Phase A2 (`-D`). Reachable tips only (`git branch -d`).
- `/iflow-status` — end report.
- `cycle_status.md` / `auto_status.md` — pattern for
  `drive_status.md` (not an `issue<N>_*` group).
- Toolbox: nothing for orchestration. Graph unused (compose skills).

## Approach

### Surface

New skill/command **`/iflow-drive <N>`** (chat: `iflow drive <N>`).

Tokens:

- **`<N>`** — existing issue = epic anchor (required).
- **`grill` / `grill-me`** — run grill-me on the epic goal before
  confirming the draft. Else auto-set `Status: confirmed` after draft
  (also honour project `grill_me_default`).
- **`loops:<n>`** — forwarded to `/iflow-auto`.
- **`dry-run`** — show planned stages/queue; no writes, no confirm.
- **`abort` mid-run** — not a start token; any user message that *is*
  (or starts with) `abort` / `stop` / `cancel` / `halt` (case-
  insensitive, optional leading `/`) **stops** at the next stage /
  issue boundary. Record `aborted` in `drive_status.md`. Same floor as
  cycle `onfail:stop` (clean default branch).

### Sequence (after confirm)

1. **Draft epic.** `/iflow-epic <N>` (write-free on GitHub). If
   `epic<N>_plan.md` already `confirmed`, skip. If draft exists, reuse
   unless user asked to revise. Grill only when token / baked default.
   Else set `Status: confirmed` without a second plan-accept prompt
   (covered by drive confirm).
2. **Publish all stages.** Loop `/iflow-epic <N> publish` until no
   unpublished specs. Idempotent `Published: #<M>` lines. Drive confirm
   replaces per-stage publish confirm. Commit `Published:` lines on a
   chore/issue branch or tiny PR — **not** unpushed on default (#303).
3. **Auto each part.** While `epic-status` has unfinished published
   stages: `/iflow-auto <N>` (same overnight auth). Honour
   `epoch_gated` / budget ask / cycle stops. Append created/reopened
   numbers to `drive_status.md` (`findings:`).
4. **Final review.** When every published stage is `done` (or user
   accepted a budget ask): one more adversarial pass
   (`/iflow-auto <N> review`). Create/reopen GitHub issues for
   remaining gaps (same auto table). Do **not** start another epoch
   unless the user later runs auto themselves.
5. **Cleanup.** `/iflow-cleanup` with `local only` **and** skip A2:
   switch/FF/fetch, `worktree-remove` for `reachable` only,
   `git branch -d` on `reachable` only. Leave `squash_landed` /
   `merged_pr_divergent` / `unique_work`.
6. **Report.** Summarize stages, PRs, findings issues, cleanup counts.
   Then run `/iflow-status`.

Durable file: `.issueflows/01-current-issues/drive_status.md`
(anchor, checklist of steps, findings numbers, `aborted` / `done`).

### Wiring

Register `iflow_drive` / `iflow-drive` next to auto in
`templating.py` (`COMMAND_NAMES`, `DEFAULT_SKILL_DIRS`). Standard
mode `skills = "all"` picks it up. Invocation table + rules +
workflow doc: off-path, never auto-dispatched.

## Files to touch

- `src/issue_flow/templates/skills/iflow_drive/SKILL.md.j2` (new)
- `src/issue_flow/templates/commands/iflow-drive.md.j2` (new)
- `src/issue_flow/templating.py` — register stems
- `src/issue_flow/templates/rules/_body.md.j2`
- `src/issue_flow/templates/docs/issue-workflow.md.j2`
- `src/issue_flow/templates/skills/iflow_iflow/SKILL.md.j2` +
  `commands/iflow.md.j2` — list among explicit-only
- `.issueflows/04-designs-and-guides/drive-mode.md`
- `tests/test_templating.py`, `tests/test_init.py` — render +
  off-path listing; abort tokens; cleanup `-d` only / no `-D`

No new CLI subcommand (orchestration stays in the skill, like auto).

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/`.

- Stem registered; skill/command render; `/iflow-drive` in dispatcher
  off-path list and rules.
- Skill text: compose epic → publish loop → auto → final review →
  cleanup `local only` + no A2 → status; abort tokens; grill opt-in;
  #303 Published-off-default.
- `verify_scaffold.py` only if it asserts an exhaustive command list
  that would break.

## Open questions

1. **Name.** Recommended **`/iflow-drive`**. Alts: `iflow-auto-all`,
   `iflow-epic-run`.
2. **Cleanup `-d` only** leaves squash-landed locals (this repo).
   Confirm that is intended (issue text).
3. **Budget ask mid-drive.** Auto still stops and asks accept / grant
   / abort. Drive treats that as a planned interruption (not a
   failure). OK?
4. **Existing confirmed epic.** Skip draft/publish; jump to auto.
   OK?
