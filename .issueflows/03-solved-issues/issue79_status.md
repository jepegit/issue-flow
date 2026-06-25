# Status for issue #79: new Cursor conventions

## Done checklist

- [x] Done

## What changed

- Cursor is now skills-first: the Cursor profile emits `.cursor/skills/`, `.cursor/rules/issueflow-rules.mdc`, `AGENTS.md`, and docs, but no `.cursor/commands/`.
- The dispatcher skill now writes to `.cursor/skills/iflow/SKILL.md`; the old `iflow-iflow` skill folder is pruned during update.
- `issue-flow update` prunes only known generated Cursor command files and preserves unrelated user commands.
- README, generated workflow docs, design notes, tracked Cursor scaffold, and tests now describe the new convention.

## Verification

- `uv run ruff check src/ tests/`
- `uv run pytest`
- Throwaway `issue-flow init` check: confirmed `.cursor/skills/iflow/SKILL.md` and `.cursor/rules/issueflow-rules.mdc` exist, and `.cursor/commands/` is absent.
- Throwaway `issue-flow update` migration check: confirmed generated `iflow*.md` command files are removed, unrelated `my-command.md` is preserved, old `iflow-iflow` is removed, and new `iflow` skill exists.
- `graphify update . --force`
