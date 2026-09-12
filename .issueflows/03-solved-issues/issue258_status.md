# Issue #258 status — Iterative fixes: agent-name-issue-no-confirm

Interactive `/iflow-fix` session. Individual fixes logged below; land via `/iflow-close`.

- [x] Done

## Iterative fixes log

- **2026-09-12** — Added `[issueflow].fix_auto_name` knob (default `false`; env `ISSUEFLOW_FIX_AUTO_NAME`). When true, `/iflow-fix` lets the agent invent the session title/slug without a separate naming confirm; create issue+branch still confirms. Enabled here as `fix_auto_name = true`.
- **2026-09-12** — CLI: `issue-flow config show [KEY]` (effective or `--persisted`), `config set KEY VALUE`, and `config edit` (opens `$VISUAL`/`$EDITOR`, `--create` to seed). Shared helpers in `config_ops.py`.

## Close

- Version bump: `0.4.12` → `0.4.13` (patch; stable channel).
- Landed via `/iflow-close bump`.
