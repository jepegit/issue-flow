# Global vs local packaged skills

**Issue:** [#282](https://github.com/jepegit/issue-flow/issues/282) /
[#293](https://github.com/jepegit/issue-flow/issues/293) /
epic [#269](https://github.com/jepegit/issue-flow/issues/269)
**Status:** decided 2026-09-17 (Stage 1); `both` materialize shipped
[#293](https://github.com/jepegit/issue-flow/issues/293). Honour
[user-global-config.md](./user-global-config.md).

## Context

User-global config (#281) is the contract for knobs / lock / registry /
`update --all`. This doc answers the leftover product question: which
**packaged skill stems** may also land in the editor's user-global
skill dir, and which stay project-local. Local always wins when both
exist.

## Placement values

| Value | Meaning |
|-------|---------|
| `local` | Write only under `<repo>/<agent_dir>/skills/<output>/`. |
| `global` | Write only under the editor's user-global skill dir. |
| `both` | Write the user-global copy **and** keep the project copy. Project dir with the same output name beats the user-global copy. |

No stem is `global`-only in v1: a fresh clone must still work without
a prior `update --all` or home-dir install.

## Editor user-global paths (verified 2026-09-17)

| Editor | User-global write target | Also reads (compat) | Notes |
|--------|--------------------------|---------------------|-------|
| Cursor | `~/.cursor/skills/<output>/` | Project `.cursor/skills/`, `.agents/skills/`; compat `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, `~/.codex/skills/`; user `~/.agents/skills/` | Official docs: [Cursor Agent Skills](https://cursor.com/docs/skills). **Cloud Agents sync only `~/.cursor/skills/`** — do not install Cursor globals into `~/.claude/skills/` as the primary path. |
| Claude Code | `~/.claude/skills/<output>/` | Project `.claude/skills/` | Comment hypothesis on #269 (`Cursor reads ~/.claude/skills/`) is **true for Cursor compat**, but Claude's own global dir is still `~/.claude/skills/`. |
| Codex | `~/.agents/skills/<output>/` | Legacy `~/.codex/skills/` still scanned | Current Codex docs prefer `~/.agents/skills`. Do not write the legacy path as primary. |
| opencode | `~/.config/opencode/skills/<output>/` | Compat `~/.claude/skills/`, `~/.agents/skills/` | Official docs: [OpenCode Agent Skills](https://opencode.ai/docs/skills/) (verified 2026-09-17). Primary write is XDG `~/.config/opencode/skills/`. Do not write opencode globals into `~/.claude/skills/` or `~/.agents/skills/` as the primary path. |

WSL uses the Linux home inside the distro (`~/.cursor/skills/`), not
the Windows `%USERPROFILE%` tree — same split as
[user-global-config.md](./user-global-config.md). Native Windows
opencode globals are `%APPDATA%\opencode\skills\`. No `/mnt/c` bridge
(#298).

**Local wins.** A project skill directory with the same output name
beats the user-global copy. Honour #276 stamps on **each** tree that
`update` writes: project stamps in
`.issueflows/agent/skill-stamps.json`; user-global stamps in
`$XDG_CONFIG_HOME/issue-flow/skill-stamps.json` (or
`~/.config/issue-flow/skill-stamps.json` / `%APPDATA%\issue-flow\skill-stamps.json`),
keys like `cursor/caveman`. `--force` is `overwrite_foreign` on both
trees.

## Stem table

Stems from `DEFAULT_SKILL_DIRS` + `PSTACK_SKILL_DIRS` in
`src/issue_flow/templating.py`. Output name is `skill_output_name`
(`iflow_iflow` → `iflow`; pstack keeps upstream names).

### Lifecycle (`iflow_*`) — `local`, except `iflow_init`

Bound to this repo's mode, `.issueflows/` tree, and the issue-flow
version that last ran `update`. A machine-wide lifecycle copy would
skew across repos on different versions.

**Exception (#310):** `iflow_init` is `both`. The skill is the
chicken-egg entry point (you need it to run init; you need init to
get project skills). The user-global copy lets `iflow init` run in a
folder with no scaffold yet; the project copy still wins inside a
repo (version / mode accurate). First machine still needs one CLI
`init` / `update` or `uvx issue-flow workspace bootstrap` to plant
the global copy. Other `iflow_*` stems stay `local`.

| Stem | Output | Placement |
|------|--------|-----------|
| `iflow_iflow` | `iflow` | `local` |
| `iflow_setup` | `iflow-setup` | `local` |
| `iflow_pick` | `iflow-pick` | `local` |
| `iflow_init` | `iflow-init` | `both` |
| `iflow_capture` | `iflow-capture` | `local` |
| `iflow_comments` | `iflow-comments` | `local` |
| `iflow_plan` | `iflow-plan` | `local` |
| `iflow_build` | `iflow-build` | `local` |
| `iflow_pause` | `iflow-pause` | `local` |
| `iflow_close` | `iflow-close` | `local` |
| `iflow_cleanup` | `iflow-cleanup` | `local` |
| `iflow_pr_sync` | `iflow-pr-sync` | `local` |
| `iflow_yolo` | `iflow-yolo` | `local` |
| `iflow_ops` | `iflow-ops` | `local` |
| `iflow_fix` | `iflow-fix` | `local` |
| `iflow_issue` | `iflow-issue` | `local` |
| `iflow_split` | `iflow-split` | `local` |
| `iflow_status` | `iflow-status` | `local` |
| `iflow_workspace_git` | `iflow-workspace-git` | `local` |
| `iflow_doctor` | `iflow-doctor` | `local` |
| `iflow_review` | `iflow-review` | `local` |
| `iflow_archive` | `iflow-archive` | `local` |
| `iflow_epic` | `iflow-epic` | `local` |
| `iflow_cycle` | `iflow-cycle` | `local` |
| `iflow_auto` | `iflow-auto` | `local` |
| `iflow_drive` | `iflow-drive` | `local` |
| `iflow_version_bump` | `iflow-version-bump` | `local` |
| `iflow_history_update` | `iflow-history-update` | `local` |
| `iflow_graphify` | `iflow-graphify` | `local` |

### Behaviour (standard surface, not a slash lifecycle) — `both`

User-style / cheatsheet skills are useful outside a single repo.
Keep the project copy so `standard` mode stays self-contained.

| Stem | Output | Placement |
|------|--------|-----------|
| `caveman` | `caveman` | `both` |
| `grill_me` | `grill-me` | `both` |
| `gh_ci` | `gh-ci` | `both` |

### pstack (optional) — all `local`

Opt-in via `[issueflow].pstack_skills`. Not in mode `"all"`. See
[pstack-skills.md](./pstack-skills.md).

| Stem | Output | Placement |
|------|--------|-----------|
| `pstack_unslop` | `unslop` | `local` |
| `pstack_tdd` | `tdd` | `local` |
| `pstack_blast_radius` | `blast-radius` | `local` |
| `pstack_technical_writing` | `technical-writing` | `local` |
| `pstack_bro` | `bro` | `local` |
| `pstack_principle_prove_it_works` | `principle-prove-it-works` | `local` |
| `pstack_principle_subtract_before_you_add` | `principle-subtract-before-you-add` | `local` |
| `pstack_principle_fix_root_causes` | `principle-fix-root-causes` | `local` |
| `pstack_principle_test_behavior_not_implementation` | `principle-test-behavior-not-implementation` | `local` |

## Materialize (`init` / `update` / `update --all`)

`init` and `update` (including each `update --all` member) write the
`both` stems into **every** editor user-global path above, and keep
the project copy. `--editor` still selects only the **project** tree.
Stems omitted by the active mode (e.g. `simple`) are not written. No
`global`-only stems. Not a skillbook library
([skillbook-lessons.md](./skillbook-lessons.md)). A Cursor-only
`update` still plants `iflow-init` in `~/.agents/skills/` and
`~/.claude/skills/` so switching harness does not need a second
`--editor` pass (issue #339).

Do **not** collapse Cursor + Claude into one shared `~/.claude/skills/`
tree: Cursor Cloud sync is `~/.cursor/skills/` only.

## Later

- Any future `global`-only stems (none in v1). `iflow_init` is `both`,
  not `global`-only: a fresh clone still gets the project copy.

## Link

Epic plan: `.issueflows/05-epics/epic269_plan.md`.  
User-global knobs: [user-global-config.md](./user-global-config.md).  
Editor profiles: [editor-profiles.md](./editor-profiles.md).
