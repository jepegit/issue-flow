# Status — #293

- [x] Done

## Done

- `init` / `update` write `caveman`, `grill-me`, `gh-ci` into the selected
  editor's user-global skill dir and keep the project copy.
- Stamps: `$XDG_CONFIG_HOME/issue-flow/skill-stamps.json` (keys
  `editor/output`). `--force` is `overwrite_foreign` on that tree.
- Per-editor paths: Cursor `~/.cursor/skills`, Claude `~/.claude/skills`,
  Codex `~/.agents/skills`, opencode `~/.config/opencode/skills`.
- Tests isolate `HOME` / `XDG`; foreign global skipped without `--force`.
- Docs: `configuration.md`, `global-vs-local-skills.md`,
  `user-global-config.md`. HISTORY line.

## Remaining

None.
