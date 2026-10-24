# Plan — issue #406: cut noise

Confirmed by the user in chat (2026-10-24): breaking changes allowed, no aliases,
merged commands with modes, one large issue, run end-to-end without intervention.
`issue-flow update` must migrate an existing project in one run.

## New surface (11 lifecycle skills)

| Skill | Absorbs | Side files (progressive disclosure) |
|---|---|---|
| `iflow` | iflow | — |
| `iflow-setup` | setup, init | `harness.md` |
| `iflow-pick` | pick, capture, comments | `capture.md`, `comments.md` |
| `iflow-plan` | plan | — |
| `iflow-build` | build | — |
| `iflow-pause` | pause | — |
| `iflow-close` | close, ops, version-bump, history-update, gh-ci | `merge.md`, `ops.md`, `version.md`, `changelog.md`, `ci.md` |
| `iflow-cleanup` | cleanup, pr-sync, archive | `github.md`, `prs.md`, `archive.md` |
| `iflow-run` | yolo, cycle, auto, drive | `yolo.md`, `cycle.md`, `auto.md`, `drive.md` |
| `iflow-issue` | issue, fix, epic, split, review | `new.md`, `fix.md`, `epic.md`, `split.md`, `review.md` |
| `iflow-status` | status, doctor, workspace-git, graphify | `doctor.md`, `git.md`, `graph.md` |

Behaviour skills `caveman`, `grill-me` stay. `gh-ci` folds into `iflow-close/ci.md`.
pstack stays optional. User-global "both" stems: `caveman`, `grill_me`, `iflow_setup`.

## Python

1. `templating.py`: new `COMMAND_NAMES` / `DEFAULT_SKILL_DIRS`; side-file discovery
   per skill dir; manifest emits side files; `RETIRED_*` lists gain every old name;
   `STEM_RENAMES` (old skill/command stem -> new) for config migration.
2. Commands: drop the 26 full-copy command templates. Claude Code invokes skills
   as `/name`, so the claude profile becomes skills-first (`commands_dir=None`,
   prune old `.claude/commands/iflow*.md`). opencode keeps thin wrapper command
   files from one template.
3. `skill_ownership.py`: allow packaged side files; composite hash (equals the old
   hash when there are no side files, so existing stamps stay valid).
4. `modes.py` / `step_profiles.py`: map old stems silently on read; `update`
   rewrites `config.toml` (custom modes, step profiles) to new stems.
5. `update`: prune retired project, canonical, and user-global (stamped) skills;
   drop stale stamps; upsert the Linguist block in place.
6. Python strings that name old commands updated (`agent state` next_command etc).

## Templates

- Rule body rewritten to a thin core (≤ 900 words fully rendered). CLAUDE.md
  imports AGENTS.md instead of repeating the body.
- `docs/issue-workflow.md.j2` rewritten to a short reference.
- Every skill/mode file: old command names rewritten; repo-internal design-doc
  links removed. `iflow-close` and `iflow-cleanup` split so `SKILL.md` ≤ 1,600 words.

## Tests

- New `tests/test_noise_budget.py`: word budgets, skill count, no retired names.
- New migration test: scaffold old layout, run update, assert pruned + config rewritten.
- Update existing tests for new names.

## Repo noise (this repo)

- Linguist block marks `.cursor/**`, `.claude/**`, `.opencode/**`, `.codex/**`,
  `.issueflows/agent/**`, solved/partly-solved folders `linguist-generated`.
- `graphify_gitignored = true` here; `git rm -r --cached graphify-out`.
- Design docs consolidated into topic docs.
- Docs site rewritten for the new surface.
