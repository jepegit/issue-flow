# Hands-off runs and epics

`/iflow-run` (yolo, cycle, auto, drive), epics, and the confirm contracts behind them. Each section below was a separate design note; they are grouped here so the folder stays small (issue #406).

<a id="hands-off-mode"></a>

## Hands-off mode

**Issue:** [#402](https://github.com/jepegit/issue-flow/issues/402)
**Status:** decided 2026-10-05.

### Context

Drive already composes epic draft, publish, auto, final review, and
local cleanup. Each child skill still asks, and drive requires an
existing issue number. A full feature should run after one authorization,
including when the work starts as a short description.

### Decision

`[issueflow].hands_off` (default false) is a behaviour knob. It does not
add a scaffolding mode id. `issue-flow mode hands-off` sets the key and
re-renders skills through the same path as `issue-flow update`.
`issue-flow mode standard` (alias `off`) sets it false and re-renders.
`issue-flow mode` with no arguments prints the effective value for the
current project.

Turning the knob on is the authorization. The command prints that the
next drive may auto-merge (per `cycle_nonyolo`) and delete local
branches (`-d` reachable, `-D` squash-landed) and asks once unless
`--yes`.

While the knob is on:

- `/iflow-drive`, `/iflow-yolo`, `/iflow-cycle`, and `/iflow-auto` skip
  their up-front confirms. Child confirms those skills repeat (epic
  publish, auto overnight, cycle queue, yolo confirm, cleanup A1/A2
  when the `drive` token is passed) are already authorized.
- `/iflow-drive <short description>` runs grill-me, creates one
  epic-anchor issue (same shape as `/iflow-issue epic`), then drives
  that number. A non-integer still stops and asks for `<N>` when the
  knob is off.
- AST graphify (`issue-flow graphify -C <project_root>`, never
  `extract`) runs before the epic draft and before each child
  `/iflow-plan`, even when `auto_graphify_on_plan` and
  `graphify_gitignored` are false. A missing or failing graphify is
  reported; planning continues with grep.
- A spent auto loop budget records `accepted` and continues to the
  epoch gate and final review.

Interactive `/iflow-pick`, plan Accept, `/iflow-build`, and ordinary
close still ask. Safety stops stay: unfixable failure, refused merge,
non-fast-forward that `sync-branch` cannot resolve, dirty product tree,
and `abort` / `stop` / `cancel` / `halt`. Never weaken yolo safeguards.
Never `-D` `unique_work`. Never Phase B. Never rebase or force-push the
default branch. `yolo: no` stays a lane (`cycle_nonyolo`).

Precedence matches `grill_me_default`: project `config.toml`, then
user-global, then `ISSUEFLOW_HANDS_OFF`, then the default. The switch
is per project (the working directory), not a rewrite of every
registered repo.

### Alternatives

- A new `[modes.hands-off]` scaffolding id. Rejected: `mode` already
  chooses which skills exist (`standard` / `novice` / `simple`).
- Regex-rewrite of installed skill files. Rejected: Jinja plus
  `issue-flow update` already bake knobs.
- Keep yolo and cycle confirms unless the caller is drive. Rejected:
  those prompts live in the same rendered text.
- Stop the drive when graphify fails. Rejected: same continue-on-grep
  rule as the existing plan refresh.

### Link

Drive: [drive-mode.md](./drive-mode.md).
Knobs: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
Graphify: [graphify-integration.md](./graphify-integration.md).

<a id="advanced-auto-mode"></a>

## Advanced auto mode

**Issue:** [#169](https://github.com/jepegit/issue-flow/issues/169) (epic) /
[#191](https://github.com/jepegit/issue-flow/issues/191) (this contract)
**Status:** decided 2026-07-23 (Stage 1 design).

### Context

Want an unattended path for **large** changes: thorough planning, sequential
epochs of manageable issues, yolo execution per issue, and an adversarial check
between epochs — without inventing a second lifecycle outside issue branches +
PRs.

Scaffold **modes** (`standard` / `simple`) are unrelated; this is an
orchestration flow. See [modes.md](./modes.md).

### Decisions

#### Epochs = epic stages

v1 maps **epoch** → `/iflow-epic` **Stage**. No separate epoch file format.
Guiding docs live in `epic<N>_plan.md` (Goal / Constraints / Stage Goal /
per-issue Spec).

#### Goals at three levels

| Level | Where |
|-------|--------|
| Epic | `## Goal` in `epic<N>_plan.md` |
| Epoch / stage | Explicit **Stage Goal** (or stage paragraph that states the goal) |
| Issue | Spec includes **Goal:** (crisp acceptance someone else can verify) |

#### Overnight confirm contract

One up-front confirm before unattended run. Preconditions:

- `epic<N>_plan.md` is `Status: confirmed`
- Working tree clean on the default branch
- Project tests green

After confirm: no mid-run prompts until a **stop condition** (below) or the
adversarial **loop budget** is exhausted.

#### Orchestrator surface

Off-path skill/command **`/iflow-auto`** (Stage 1 skeleton; Stage 2 adds the
adversarial gate). Composes:

1. Select earliest unfinished published stage of epic `<N>`
2. Run `/iflow-cycle epic <N>` for that stage — yolo lane for `yolo: yes`
   issues, **non-yolo lane** for `yolo: no` ones (same chain and safeguards;
   landed per `cycle_nonyolo`: `merge` default / `pr-only` / `stop`; per-run
   `nonyolo:<policy>` forwarded from auto / drive). A `yolo: no` judgment is
   not a stop by itself (issue #386).
3. Adversarial review (Stage 2)
4. Advance or stop per loop budget

`/iflow-cleanup` stays out-of-band (same as yolo/cycle).

#### Adversarial loop budget

| Knob | Default | Notes |
|------|---------|--------|
| `[issueflow] auto_adversarial_loops` | `2` | Baked at `issue-flow update`; env `ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS` |

**Trailing override** on `/iflow-auto`: `loops:<n>` (positive integer) for this
run only. Precedence: trailing > config > default `2`.

After each inter-epoch adversarial pass, if work remains and the counter is
below the budget, re-queue and re-run adversarial. When the budget is spent,
**stop and ask**: accept current implementation / grant `N` more loops / abort.

**Manual scenario (budget ask):** overnight confirm with budget `2`; stage cycle
merges; adversarial pass finds gaps → reopen/create → `loop_count` becomes `1`;
cycle those issues again → adversarial again → still gaps → `loop_count` `2`
equals budget → **stop and ask** (accept / grant more loops / abort). Accept
leaves findings as-is; grant `N` raises the effective budget for this run and
continues; abort stops without advancing the epoch.

#### Durable state

`.issueflows/01-current-issues/auto_status.md` (name fixed here) records:

- epic number, current epoch/stage index
- adversarial loop count and budget
- last outcome (cycle merged / adversarial findings / stopped)

Not an `issue<N>_*` group — folder sweeps leave it alone. Archive when the
auto-run finishes (same idea as `cycle_status.md`).

#### Model-class hints

Published issue bodies include **`Model: deep | fast | default`**:

- `deep` — planning, adversarial review, design-heavy specs
- `fast` — mechanical / pattern-following yolo-fit work
- `default` — use the step's baked profile

Hints are advisory for agents; Stage 1 does not enforce labels. Optional later
tie-in to `deep_model_label` / `fast_model_label` (see
[step-model-directives.md](./step-model-directives.md)).

#### Adversarial review (inter-epoch)

Run after a stage's `/iflow-cycle` finishes (or via `/iflow-auto <N> review`).
Judgment stays in the agent skill; no separate CLI judge. Writes (reopen /
create) are authorized by the overnight confirm — **no mid-budget prompts**.

| Check | Pass when | Fail → action |
|-------|-----------|---------------|
| Stage goal met | Merged PRs for the stage's published issues collectively satisfy the Stage Goal / stage paragraph | Reopen incomplete issues and/or create inter-epoch blocker issues |
| Epic goal progress | No clear regression vs epic `## Goal` / Constraints | Same |
| Spec honesty | Landed work matches each issue Spec / Goal (no silent scope cut) | Reopen with concrete remaining acceptance |
| Blast radius | No unplanned shared-file / API breaks outside the stage queue | Create blocker issue(s) with Spec + `Depends on` + `Part of epic #<N>` |

**Actions:** prefer `gh issue reopen <M>` (+ comment) when an existing stage
issue still owns the gap; `gh issue create` only for cross-cutting / new work.
Created blockers include **`Model: deep`**, clear Spec/Goal, resolved
`Depends on`, and `Part of epic #<N>.` — **no new label** in v1 (avoid sprawl).

**`auto_status.md` outcomes:**

- `adversarial_clear` — findings empty; hand off to next-epoch gate (separate)
- `adversarial_findings` — list reopened/created numbers + short gap notes;
  then **loop control** (increment `loop_count`, re-queue or budget ask)
- `budget_ask` — loop budget exhausted; waiting on user (accept / grant / abort)
- `accepted` / `aborted` — user answered the budget ask

Standalone `/iflow-auto <N> review` without a prior overnight authorization in
`auto_status.md` asks once (same confirm shape), then proceeds. Loop control
still applies after findings when a budget is recorded.

#### Next-epoch gate

Before starting stage `k+1`, require stage `k` **clear**:

- `issue-flow agent epic-status <N> --json`: stage `k` has `done: true` (all
  published issues closed), and
- no open inter-epoch blocker numbers still listed in `auto_status.md` findings

If not clear: set `last_outcome: epoch_gated`, report open numbers, **do not**
start `k+1`. If clear and a later unfinished published stage exists, continue
under the same overnight authorization (reset `loop_count` for the new epoch).
If every published stage is done: `last_outcome: complete`.

#### Stop conditions (unattended)

Same floor as `/iflow-cycle` / `/iflow-yolo`: unfixable test/lint failure,
refused merge / non-ff pull that `agent sync-branch` cannot resolve (it takes
additive `HISTORY.md` / design-guide / status-file conflicts and squash-landed
stacked parents), ambiguous or contradictory spec (not-small is advisory on
the non-yolo lane), action outside the confirmed queue. "Already merged" is a
success. Never weaken a yolo safeguard to keep moving.

### Non-goals

- Parallel adversarial agents
- Silent confirm of novel large plans (planning still needs a confirmed epic)
- Replacing `/iflow-epic` / `/iflow-cycle` / `/iflow-yolo`
- GitLab
- Auto-running `/iflow-cleanup`

### Link

Epic plan: `.issueflows/05-epics/epic169_plan.md`.  
Knobs: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).  
Cycle: [label-driven-flows.md](./label-driven-flows.md),
[parallel-cycle.md](./parallel-cycle.md).

<a id="drive-mode"></a>

## Drive mode

**Issue:** [#306](https://github.com/jepegit/issue-flow/issues/306)
**Status:** decided 2026-09-19.

### Context

Want one off-path command that takes an **existing** GitHub issue and
runs the whole large-change path: epic draft → publish every stage →
`/iflow-auto` each epoch → a final review that creates leftover
findings → local cleanup (`-d` only) → `/iflow-status`.

This is **compose-only**. It does not replace `/iflow-epic`,
`/iflow-auto`, `/iflow-cycle`, or `/iflow-yolo`.

### Decisions

#### Surface

Off-path skill/command **`/iflow-drive <N>`** (chat: `iflow drive <N>`).

`<N>` is already on GitHub and becomes the epic anchor. Drive never
creates the anchor (`/iflow-issue epic` is the path when none exists).

#### Confirm contract

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

#### Carry-through (issue #386)

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

#### Grill

`grill` / `grill-me` token **or** baked `grill_me_default` → run
grill-me on the epic goal before draft-accept. Otherwise auto-confirm
the draft under the drive confirm.

#### Existing confirmed epic

If `epic<N>_plan.md` is already `Status: confirmed`, skip draft and
publish; jump to `/iflow-auto`.

#### Publish and #303

`Published: #<M>` lines must land on a chore/issue branch or tiny PR —
never as unpushed commits on home default. Same rule as `/iflow-epic`
publish (issue #303).

#### Auto each part

While `epic-status` has unfinished published stages, run `/iflow-auto
<N>` (forward `loops:<n>` and `nonyolo:<policy>`). Honour
`epoch_gated`. A `yolo: no` child is not a stop (see carry-through).
Append created / reopened numbers to `drive_status.md` `findings:`.

#### Final review

When every published stage is `done` (or the user accepted a budget
ask): `/iflow-auto <N> review`. Create/reopen leftover findings using
the [advanced-auto-mode.md](./advanced-auto-mode.md) criteria table.
Do **not** start another epoch from drive.

#### Cleanup (`-d` + `-D` under the drive confirm)

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

#### Abort tokens

Any user message that *is* (or starts with) `abort` / `stop` /
`cancel` / `halt` (case-insensitive, optional leading `/`) stops at
the **next stage or issue boundary**. Record `aborted` in
`drive_status.md`. Same floor as cycle `onfail:stop`.

#### Durable state

`.issueflows/01-current-issues/drive_status.md` (name fixed here):

- anchor number
- checklist: `draft` / `publish` / `auto` / `final_review` / `cleanup`
  / `status`
- `findings:` (created / reopened numbers)
- last outcome: `pending` / `aborted` / `done`

Not an `issue<N>_*` group — folder sweeps leave it alone.

### Hands-off knob

`issue-flow mode hands-off` is a separate project behaviour knob, not a
new drive subcommand. When `[issueflow].hands_off` is on, the confirm
above is already authorized, a short description may create one epic
anchor after grill-me, and a spent auto loop budget records accept.
See [hands-off-mode.md](./hands-off-mode.md).

### Non-goals

- New CLI subcommand
- Forking yolo / cycle / auto / epic internals
- Auto-dispatch from `/iflow`
- Phase B (remote deletes / findings issue) from drive
- `-D` on `unique_work`, ever
- Creating the epic anchor

### Link

Auto: [advanced-auto-mode.md](./advanced-auto-mode.md).
Cleanup: [local-branch-cleanup.md](./local-branch-cleanup.md).
Default diverge: [default-branch-diverge.md](./default-branch-diverge.md).

<a id="parallel-cycle"></a>

## Parallel cycle dispatch (experimental)

Context: issue #143 — the cycling-mode epic (#145) stage 3. When the editor
harness supports background execution, **provably independent** issues in a
cycle could run in parallel. This is deliberately the last slice and stays
**opt-in and experimental**: parallelism multiplies failure modes, and the
sequential cycle must always work everywhere without it.

### Hard constraints

- **Only independent issues qualify.** Use `issue-flow agent queue --json`:
  an issue is eligible only when it appears in the `independent` list — i.e.
  it has **no dependency relation, in either direction, to any other queue
  member**. Anything with an edge (even to a blocked relative) runs
  sequentially.
- **Sequential remains the default and is never weakened.** Parallelism is
  requested explicitly (`parallel:<n>`); with no such token the cycle runs
  exactly as before. No safeguard is relaxed to enable parallelism.
- **Merges are serialized.** PRs never merge concurrently. The coordinating
  session merges them one at a time on the default branch, rebasing / re-running
  tests on a refusal. Concurrent merges race on the default branch and on CI.
- **Shared files are written only by the coordinator, in merge order.** The
  worst offender is `HISTORY.md`: parallel workers must **not** each
  edit it. Each worker leaves its changelog bullet in its own issue status
  file (or PR body); the coordinator appends the bullets to `HISTORY.md`
  during the serial merge step, in the order merges land — the same ordering
  rule as the changelog conflict resolver (newest bullet last), so serial and
  parallel runs produce the same file. A worker PR that still goes `DIRTY` on
  `[Unreleased]` is resolved with `issue-flow agent sync-branch`, never by
  hand-editing conflict markers; see
  [changelog-conflicts.md](./changelog-conflicts.md) (issue #240).

### Execution pattern (per-issue worktree)

1. Resolve the independent subset from `agent queue`.
2. For each, `git worktree add ../<repo>-<N> <N>-<slug>` so every issue gets
   an isolated working tree on its own branch — no shared index, no collisions.
3. Print each worktree path with
   `issue-flow agent open-workspace <worktree> --json`. Skills do not
   launch a window — see [separate-workspaces.md](./separate-workspaces.md).
4. Run the yolo chain (minus its own merge/close-to-default steps) in each
   worktree, in the background where the harness allows.
5. **Serial merge queue:** the coordinator opens/merges each PR one at a time
   (`--squash`), pulling the default branch between merges; on a non-fast-forward
   or CI refusal it rebases that branch and retries, or falls back to sequential
   for the remainder.
6. Append the deferred `HISTORY.md` bullets in merge order, then
   `git worktree remove` each worktree.

### Per-harness notes (capabilities move fast — verify before relying)

- **Cursor** — background agents / parallel chats can drive worktrees; there is
  no first-class "wait for all" primitive, so the coordinator polls PR state.
- **Claude Code** — subagents and `git worktree` support make the
  worktree-per-issue pattern natural; the parent session is the coordinator.
- **opencode / Codex** — background execution varies; when unavailable, refuse
  `parallel:<n>` and run sequentially.

Detection is best-effort: if the skill cannot confirm the harness supports
background execution, it **refuses `parallel:<n>` and runs sequentially** —
never silently pretending to parallelize.

### Out of scope

- **Cross-repo parallel cycles** — combining this with the workspace registry
  (multiple member repos in one run) is a possible follow-up, not covered here.
- Any weakening of the sequential path.

<a id="epic-start"></a>

## Epic start session (`/iflow-epic start`)

**Issue:** [#333](https://github.com/jepegit/issue-flow/issues/333)
**Status:** decided 2026-09-23.

### Context

After an epic child lands, `/iflow` lists `next_candidates` and
**recommends** `/iflow-pick` ([iflow-epic-awareness.md](./iflow-epic-awareness.md),
#210). That is correct (pick creates a branch) but clumsy: the user already
knows they are mid-epic and must type `iflow pick <N>` every time.

`/iflow-drive`, `/iflow-auto`, and `/iflow-cycle epic <N>` already cover
unattended / stage-batch runs. A fifth executor would be a mistake.

### Decision

#### Surface

`/iflow-epic start [N]` (chat: `iflow epic start [N]`). Same skill as
`/iflow-epic`. No new stem.

#### Resolve `N`

Explicit number wins. Else list in-flight confirmed epics, drafts, and
“create new” (`/iflow-issue epic`). **Exactly one** live epic with work
left → preselect it, still confirm.

#### Prepare

Deterministic only: `issue-flow agent epic-status <N> --json` → stage,
blockers, `next_candidates`, unpublished specs. No silent publish, no
silent `worktree-add`.

#### Session

`.issueflows/01-current-issues/epic_session.md`:

```text
epic: <N>
mode: one-and-ask
```

`/iflow-epic stop` (or `abort`) clears it. Run `start` again to change
mode. v1 writes **`one-and-ask` only** as the session default.

#### one-and-ask

When **session present** + **no focus** + `next_candidates`:

1. Stop. Ask: next `#<M>` — **continue** / switch to cycle|auto|drive / **stop**.
2. **Continue** = today’s pick chain (confirm branch/worktree + capture).
   Never silent-pick. Child `yolo` / `ops` labels still apply.
3. Typed `iflow pick 12` still works.

`/iflow` **without** a session is unchanged (#210): list candidates,
recommend pick. Never auto-dispatch pick.

When `noob` is on, the footer uses this same split (`epic_session` +
`epic_hint`, not raw `next_command`) so **Recommended** is `/iflow` or
`/iflow-pick` — not `none` or `/iflow-capture`. Unpublished current
stage → `/iflow-epic <N> publish`. See `#337`.

#### Run-style menu (state-dependent)

Hand off to existing primitives. No new batcher.

| Offer | Primitive |
|-------|-----------|
| This stage, yolo each issue | `/iflow-cycle epic <N> [stage k]` |
| Rest of epic, review between stages | `/iflow-auto` / `/iflow-drive` |
| Stay one-and-ask | write session; wait for next `/iflow` |

Adversarial review = existing auto/drive only. No parallel adversary
agents.

Menu depends on epic state (no plan / draft / unpublished stage /
`next_candidates` / budget ask). Do not offer “drive the whole epic”
as a new engine when drive already exists.

### Alternatives considered

- Auto-dispatch `/iflow-pick` from `/iflow` — rejected (#210): pick
  creates branches.
- New “run whole epic” executor — rejected; compose drive/auto/cycle.
- Parallel adversarial agents — rejected; keep sequential inter-epoch
  review.
- Session default `manual` (auto-advance after close) — rejected in
  favour of **one-and-ask**.

### Non-goals (v1)

Silent pick. New batcher. Creating an epic anchor from a vibe (use
`/iflow-issue epic`). Phase A2 cleanup from start.

### Related

- [iflow-epic-awareness.md](./iflow-epic-awareness.md) (#210)
- [advanced-auto-mode.md](./advanced-auto-mode.md)
- [drive-mode.md](./drive-mode.md)

<a id="iflow-epic-awareness"></a>

## `/iflow` epic awareness

**Issue:** [#210 — Iflow in epics](https://github.com/jepegit/issue-flow/issues/210)
**Related:** [#139](https://github.com/jepegit/issue-flow/issues/139) (`/iflow-pick` epic preference + stage gates)

### Context

`/iflow-pick` already surfaces an active epic’s current-stage
`next_candidates` via `issue-flow agent epic-status`. Plain `/iflow` /
slash-less `iflow` did not: with no focus issue it fell through to
`/iflow-init` and asked for a number, which feels broken mid-epic.

### Decision

When `/iflow` has **no resolvable focus** (no `^\d+-.+` branch, empty
`01-current-issues/`):

1. Read `epic_hint` from `issue-flow agent state --json` (or scan
   `05-epics/` + `epic-status` as fallback).
2. If any `next_candidates` → **stop**, list them, recommend `/iflow-pick`.
   Never auto-dispatch pick; never silent-pick even for one candidate.
   Trailing explicit `N` may still dispatch `/iflow-init <N>`.
3. If none → today’s state A → `/iflow-init`.

With a resolved focus, A/B/C/D dispatch is unchanged. Soft report hint
after close when an epic still has candidates is optional.

### CLI

`agent state --json` includes `epic_hint: { epics: [...] }` only when
there is no focus (and focus is not ambiguous). Each entry:
`epic`, `title`, `stage`, `stage_title`, `next_candidates`.

### Non-goals

- Auto-dispatch to `/iflow-pick` / `/iflow-cycle` / `/iflow-auto`
- Changing epic publish or stage-gate offers (#139)

An **opt-in** epic session (`/iflow-epic start`) that asks before
starting the next candidate is [epic-start.md](./epic-start.md) — it
does not change the no-session `/iflow` behaviour above.
