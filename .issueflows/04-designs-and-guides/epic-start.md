# Epic start session (`/iflow-epic start`)

**Issue:** [#333](https://github.com/jepegit/issue-flow/issues/333)
**Status:** decided 2026-09-23.

## Context

After an epic child lands, `/iflow` lists `next_candidates` and
**recommends** `/iflow-pick` ([iflow-epic-awareness.md](./iflow-epic-awareness.md),
#210). That is correct (pick creates a branch) but clumsy: the user already
knows they are mid-epic and must type `iflow pick <N>` every time.

`/iflow-drive`, `/iflow-auto`, and `/iflow-cycle epic <N>` already cover
unattended / stage-batch runs. A fifth executor would be a mistake.

## Decision

### Surface

`/iflow-epic start [N]` (chat: `iflow epic start [N]`). Same skill as
`/iflow-epic`. No new stem.

### Resolve `N`

Explicit number wins. Else list in-flight confirmed epics, drafts, and
“create new” (`/iflow-issue epic`). **Exactly one** live epic with work
left → preselect it, still confirm.

### Prepare

Deterministic only: `issue-flow agent epic-status <N> --json` → stage,
blockers, `next_candidates`, unpublished specs. No silent publish, no
silent `worktree-add`.

### Session

`.issueflows/01-current-issues/epic_session.md`:

```text
epic: <N>
mode: one-and-ask
```

`/iflow-epic stop` (or `abort`) clears it. Run `start` again to change
mode. v1 writes **`one-and-ask` only** as the session default.

### one-and-ask

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

### Run-style menu (state-dependent)

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

## Alternatives considered

- Auto-dispatch `/iflow-pick` from `/iflow` — rejected (#210): pick
  creates branches.
- New “run whole epic” executor — rejected; compose drive/auto/cycle.
- Parallel adversarial agents — rejected; keep sequential inter-epoch
  review.
- Session default `manual` (auto-advance after close) — rejected in
  favour of **one-and-ask**.

## Non-goals (v1)

Silent pick. New batcher. Creating an epic anchor from a vibe (use
`/iflow-issue epic`). Phase A2 cleanup from start.

## Related

- [iflow-epic-awareness.md](./iflow-epic-awareness.md) (#210)
- [advanced-auto-mode.md](./advanced-auto-mode.md)
- [drive-mode.md](./drive-mode.md)
