# Issue #293: Materialize both stems into per-editor user-global skill dirs

Source: https://github.com/jepegit/issue-flow/issues/293

## Original issue text

### Problem / context

Epic #269 Stage 3: packaged `both` stems (`caveman`, `grill-me`, `gh-ci`) should install into the editor's user-global skill dir as well as the project copy. Local still wins. Not a skillbook library.

### Spec

On `init` / `update` (and each `update --all` member), write `both` stems to the **per-editor** user-global path from [global-vs-local-skills.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/global-vs-local-skills.md) (#282): Cursor `~/.cursor/skills/`, Claude `~/.claude/skills/`, Codex `~/.agents/skills/`. Opencode: only if #292 verified a path; else skip. Keep the project-local copy (no `global`-only stems). Honour #276 on the user-global tree: stamps live under the user-global issue-flow dir (not a repo's `.issueflows/agent/skill-stamps.json`). `--force` on `update` / `update --all` is `overwrite_foreign` for those global dirs too. Do not write Cursor globals into `~/.claude/skills/`.

Tests: tmp `HOME` / `XDG`; project copy still present; foreign global dir skipped without `--force`. Docs in `docs/configuration.md` plus the two design docs.

### Goal

A machine that ran `update` has the three `both` skills in the editor global dir, and a project skill of the same name still wins.

### Model

default

### Depends on

#292

Part of epic #269.
