# Plan: #333 `/iflow-epic start` + one-and-ask

## Goal

Add `/iflow-epic start [N]` / `stop` as a session, and teach `/iflow` to
**ask** before starting the next epic child — without silent-pick and
without a new executor.

Honour `.issueflows/04-designs-and-guides/epic-start.md`.

## Constraints

- Compose only: hand off to `/iflow-pick` (Continue), `/iflow-cycle`,
  `/iflow-auto`, `/iflow-drive`. No fifth orchestrator.
- `/iflow` **without** a session stays #210: list candidates, recommend
  pick. Never auto-dispatch pick.
- Session write only after confirm. No silent publish / worktree-add.
- `epic_session.md` is not an `issue<N>_*` group — sweep/doctor ignore it
  (same as `auto_status.md`).
- No new `00-tools/` script.
- Design docs already drafted on this branch; do not rewrite the contract.

### Prior art

- `_collect_epic_hints` / `agent state` `epic_hint` (`agent.py`, #210) —
  extend with `epic_session`; do not change no-session gap behaviour.
- `issue-flow agent epic-status` — start’s prepare + live-epic listing.
- `/iflow-epic` Input today: required `<N>` + `publish [stage k]`. Add
  `start [N]` / `stop` as sibling actions; drafting default unchanged
  when the first token is a number and not `start`/`stop`/`publish`.
- `auto_status.md` in `01-current-issues/` — session file lives beside it.
- `/iflow` step 0a (`iflow.md.j2` / `iflow` skill) — branch: session
  present → one-and-ask prompt; else today’s recommend-pick.
- Label flows on pick (`yolo` / `ops`) — Continue follows pick, so
  labels still apply. Mirror / coexist: no extra routing in `/iflow`.

## Approach

1. **Session I/O.** Small helpers in `tracking.py` (or a tiny
   `epic_session.py`): read/write
   `.issueflows/01-current-issues/epic_session.md` as two keys:

   ```text
   epic: 269
   mode: one-and-ask
   ```

   Unknown mode → treat as missing (do not guess). `stop` / `abort`
   deletes the file.

2. **`agent state`.** When no focus, include
   `epic_session: {epic, mode} | null` next to `epic_hint`. If a session
   exists, still fill `epic_hint` (needed for the ask). `next_command`
   stays unset in the epic gap (not `iflow-pick`).

3. **`/iflow-epic start [N]`** (skill + command twin):
   - Parse `start` / `stop`/`abort` before the draft path.
   - Resolve `N`: explicit; else scan `05-epics/` + `epic-status`.
     Exactly one live epic (confirmed, work left: `next_candidates` or
     unpublished specs) → preselect, still confirm. Zero → offer
     `/iflow-issue epic`. Several → numbered list, wait.
   - Existing session for a **different** epic → confirm replace.
   - Prepare: print `epic-status --json` (stage, blockers,
     `next_candidates`, unpublished).
   - State-dependent **offer** (one confirm writes session and/or names
     the handoff): stay one-and-ask / cycle this stage / auto / drive /
     abort. Do not run cycle/auto/drive until that confirm.
   - `stop`: delete file, report.

4. **`/iflow` epic gap.** Session + `next_candidates` → **stop** and ask
   `next #<M> — continue / cycle|auto|drive / stop` (`<M>` = first
   `next_candidates` entry for the session epic). Continue on a **later
   turn** follows `/iflow-pick` for `#<M>` (user said continue / `yes` /
   the number). This turn writes nothing and creates no branch.
   Trailing explicit issue number still captures that `N` (#210).
   Soft close hint: if session exists, say “run `/iflow`” not only
   `/iflow-pick`.

5. **Docs.** `docs/issue-workflow.md` (+ j2), epic command help,
   `epic-start.md` already the contract (touch only if implement
   drifts). AGENTS managed block updates via `issue-flow update`.

## Files to touch

- `src/issue_flow/tracking.py` (or new `epic_session.py`) — read/write.
- `src/issue_flow/agent.py` — `epic_session` on `state`.
- `src/issue_flow/templates/skills/iflow_epic/SKILL.md.j2` +
  `commands/iflow-epic.md.j2` — `start` / `stop`.
- `src/issue_flow/templates/skills/iflow/SKILL.md.j2` +
  `commands/iflow.md.j2` — session one-and-ask; no-session unchanged.
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` (and command
  twin if it mentions pick-after-merge) — session hint.
- `docs/issue-workflow.md` + `templates/docs/issue-workflow.md.j2`.
- `tests/test_cli.py` / `test_tracking.py` (or new) / `test_templating.py`
  — parse session; state payload; rendered start/stop + gap text.

## Test strategy

`uv run pytest` and `uv run ruff check src/ tests/`.

- Session round-trip; missing/invalid file → `None`.
- `agent state` with no focus + session file → `epic_session` set;
  without file → `null`; no-session `epic_hint` still lists candidates.
- Rendered epic skill mentions `start [N]` / `stop` and “never silent-pick”.
- Rendered `/iflow` with default context: no-session still “recommend
  `/iflow-pick`”; session branch text present (one-and-ask).
- Existing #210 tests stay green.

## Open questions

1. **Several `next_candidates`:** ask about the **first** only (epic-status
   order)? Recommended: **yes**.
2. **`start` with no live epic:** only point at `/iflow-issue epic`, or
   also list draft plans? Recommended: list drafts + create-new.
3. **CLI `issue-flow agent epic-session`?** Recommended: **no** in v1 —
   file + `agent state` is enough.
