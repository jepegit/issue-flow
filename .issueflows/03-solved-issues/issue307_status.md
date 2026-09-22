# Status: #307 noob mode

- [x] Done

## What's done

- Plan accepted (`noob` knob, seed on novice, footer on installed stems).
- Knob wired: `DEFAULT_NOOB = false`, `Settings.resolve_noob`, `modes.read_noob`, `config_ops`, default `config.toml` comment, `issue-flow config` help.
- First-time `--mode novice` seeds `noob = true` via `NOVICE_CONFIG`. Existing toml never rewritten.
- Shared footer `templates/skills/_noob_next.md.j2`. `render_template` appends it when `noob` is on and stem is not `comments` / `history_update` / `version_bump`.
- Footer: run `issue-flow agent state --json`, print `next_command` as Recommended, plus stem-specific relevant `/iflow-*` list. Never auto-dispatch.
- Docs: `docs/configuration.md`, `docs/how-to/choose-a-mode.md` (`noob` ≠ `novice`), `skill-behaviour-knobs.md`.
- This repo's `config.toml` left off.
- Tests: default off; env/config flip; novice seed; footer omitted by default / appended when on.
- `uv run ruff check src/ tests/` pass. Full `uv run pytest`: 832 passed.
- HISTORY.md bullet under `[Unreleased]`.

## Remaining work

- None. Close: commit, push, PR.
