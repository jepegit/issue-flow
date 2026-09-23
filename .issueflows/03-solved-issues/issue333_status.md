# Status: #333 `/iflow-epic start` + one-and-ask

- [x] Done

## What's done

- Plan accepted (2026-09-23).
- `epic_session.py`: two-line `epic_session.md` I/O (`one-and-ask` only; unknown mode = missing).
- `agent state` always reports `epic_session`; no-session `epic_hint` / `next_command` unchanged (#210).
- `/iflow-epic start [N]` / `stop` skill + command: resolve N, confirm replace, `epic-status` prepare, hand off cycle/auto/drive. Never silent-pick.
- `/iflow` gap: session + candidates → one-and-ask; no session → recommend-pick.
- Close + noob + rules + `docs/issue-workflow` hint: run `/iflow` when session on.
- Tests: session I/O, state payload, rendered start/stop + gap. `844 passed`.
- Version `0.5.7` → `0.5.8`. HISTORY promoted.

## Remaining work

None.
