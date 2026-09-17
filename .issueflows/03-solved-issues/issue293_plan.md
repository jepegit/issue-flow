# Plan — #293 Materialize both stems into per-editor user-global skill dirs

## Approach

On `init` and `update` (including each `update --all` member), after
project surfaces, write `caveman` / `grill-me` / `gh-ci` into the
**selected editor's** user-global skill dir. Keep the project copy.
Stamps under the user-global issue-flow dir (`skill-stamps.json`, keys
`{editor_id}/{output}`). `--force` is `overwrite_foreign` on that tree.
Skip stems not in the active mode. Never write Cursor globals into
`~/.claude/skills` (or opencode into Claude/Codex compat dirs).

## Confirmation

Overnight `/iflow-auto` 269 Stage 3 authorized this yolo path.
