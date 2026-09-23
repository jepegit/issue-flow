# Issue #333: /iflow-epic start: one-and-ask session so /iflow can continue an epic without typing pick

Source: https://github.com/jepegit/issue-flow/issues/333

## Original issue text

## Problem / context

After an epic child lands, `/iflow` lists `next_candidates` and only
*recommends* `/iflow-pick` (#210). Correct (pick creates a branch) but
clumsy mid-epic. Drive / auto / cycle already cover unattended and
stage-batch runs — do not add a fifth executor.

Design: `.issueflows/04-designs-and-guides/epic-start.md`.

## Spec

- Add `/iflow-epic start [N]` (chat: `iflow epic start [N]`). Same skill.
- Resolve `N`: explicit wins; else list live epics / drafts / create-new.
  Exactly one live epic with work left → preselect, still confirm.
- Prepare: `epic-status --json` only. No silent publish or worktree-add.
- Write `.issueflows/01-current-issues/epic_session.md` (`epic`, `mode:
  one-and-ask`). `iflow epic stop` clears it.
- With session + no focus + `next_candidates`: `/iflow` asks
  “next #<M> — continue / switch to cycle|auto|drive / stop”.
  Continue = pick chain (confirm branch/worktree + capture). Never
  silent-pick. Child yolo/ops labels still apply.
- State-dependent menu hands off to existing cycle / auto / drive.
- `/iflow` without a session unchanged (#210).

## Acceptance criteria

- `iflow epic start` with no `N` and one live epic preselects it and waits.
- Session file written only after confirm; `stop` removes it.
- `/iflow` with session + candidates asks; does not create a branch until Continue.
- `/iflow` with no session still only recommends pick.
- No new batch/orchestrator primitive.

## Out of scope

Silent pick. Parallel adversary agents. New “run whole epic” engine.
Creating an anchor from a vibe (`/iflow-issue epic`). Phase A2 from start.
