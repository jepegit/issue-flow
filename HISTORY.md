# History

This file tracks notable changes to **issue-flow** per release.

Format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Release tags live on GitHub: <https://github.com/jepegit/issue-flow/releases>.
Pre-0.2.2 entries are reconstructed from git history and PR titles and may be less precise
than the GitHub release notes they link to.

## [Unreleased]

- **Dependency awareness at install time (#18).** A new `Prerequisites` section in the README documents the external CLI tools the scaffolded workflow shells out to (`git`, `gh` — with install hints per OS and a `gh auth login` reminder), and `issue-flow init` / `issue-flow update` now run a `shutil.which`-based dependency check up front. If anything is missing, the CLI prints the install hints and asks for confirmation before continuing. The prompt is auto-skipped on non-TTY stdin (CI) and can be bypassed explicitly with `--skip-dep-check`.
- `issue-flow init` now creates or extends a project `.env` with `ISSUEFLOW_*` hints (#35).
- Rename `ISSUEFLOW_CURSOR_DIR` to the more tool-agnostic `ISSUEFLOW_AGENT_DIR` (#36).
- `/issue-close` flags unrelated uncommitted changes and reminds about the issue branch after the PR is opened (#37).
- Branch and folder hygiene added to `/issue-init`, `/issue-start`, and `/issue-close`: non-destructive preflight reporting of current branch, ahead/behind counts, and working-tree state; automatic sweep of stale entries in `.issueflows/01-current-issues/` based on the `- [x] Done` marker in status files (#38, addresses #31).
- **Expanded slash-command lifecycle (#39).** Four new commands — `/issue-plan`, `/issue-pause`, `/issue-cleanup`, `/issue-yolo` — plus matching Agent Skills.
  - `/issue-plan` writes a structured `issue<N>_plan.md` (Goal, Constraints, Approach, Files to touch, Test strategy, Open questions) and requires explicit user confirmation before any code is touched. The planning step was removed from `/issue-start` (**breaking**); `/issue-start` now reads the plan file and offers to run `/issue-plan` first if it is missing (with a "proceed without plan" escape hatch for trivial work).
  - `/issue-pause` parks work mid-stream: updates the status file's **Remaining work** section, moves the issue group to `.issueflows/02-partly-solved-issues/`, and optionally makes a WIP commit and/or switches back to the default branch under a single consolidated confirm.
  - `/issue-cleanup` now owns post-merge branch hygiene (detect merge via `gh pr view`, consolidated single confirm, `git branch -d` on every local branch reachable from `origin/<default>` — never `-D`). This logic was removed from `/issue-close` step 7 (**breaking**); `/issue-close` now points users at `/issue-cleanup` after the PR merges.
  - `/issue-yolo` chains `init → plan → start → close` for small, low-risk issues with up-front safeguards (refuses on default branch, refuses with dirty unrelated changes, requires `uv run pytest` to pass, single consolidated confirm). Never chains `/issue-cleanup`.
  - **Quick start `/iflow` smart dispatcher.** Inspects the focus issue (a branch-derived `N` from an `<N>-<slug>` branch is authoritative — it wins even when `issue<N>_*` files don't exist yet or unrelated groups sit in `.issueflows/01-current-issues/`; otherwise falls back to the single group in `01-`, else asks) and dispatches to `/issue-init`, `/issue-plan`, `/issue-start`, or `/issue-close` based on which files exist and whether the status file is marked `- [x] Done`. Warns up front when the focus issue is archived under `02-partly-solved-issues/` or `03-solved-issues/` so the user knows `/issue-init`'s archived-issue guard will ask for an explicit re-open confirmation. Forwards trailing args verbatim. Never auto-dispatches to `/issue-pause`, `/issue-cleanup`, or `/issue-yolo` — those stay explicit.
- **`/issue-close` now updates `HISTORY.md` (#15).** New step between the version bump and issue-folder housekeeping, driven by a new `issueflow-history-update` Agent Skill. Appends a bullet to `## [Unreleased]` on a regular close, and on `/issue-close bump <level>` promotes `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` with a fresh empty `## [Unreleased]` above it. Opt-out via `nohistory`; override the bullet summary with `log "..."`. New config knob `ISSUEFLOW_HISTORY_FILE` (default `HISTORY.md`) lets projects point at `CHANGELOG.md` or similar.

## [0.2.2] - 2026-04-17

- `issue-flow init` now creates or extends `.env` with `ISSUEFLOW_*` hints so downstream tools pick up the same config (#34).
- Cursor Agent Skills (`issueflow-issue-init`, `issueflow-issue-start`, `issueflow-issue-close`, `issueflow-version-bump`) are scaffolded into `.cursor/skills/` by `init` / `update` (#28).
- `/issue-close` gained an optional `uv version --bump` step and a local scaffold script so contributors can preview template changes without reinstalling (#27, #30).
- `issue-flow update` now handles already-initialized projects more safely (#29).

## [0.2.1.post2] - 2026-04-16

- Packaging / metadata fix-up (no user-facing changes).

## [0.2.1.post1] - 2026-04-16

- Packaging / metadata fix-up (no user-facing changes).

## [0.2.1] - 2026-04-16

- Optional version-bump step in `/issue-close` (first cut) and 0.2.1 release plumbing (#11).
- Streamlined `/issue-init` guidance for issue body text and newline handling (#9).

## [0.2.0] - 2026-04-15

- Added Agent Skills scaffold for `issue-flow init` / `update` so Cursor can invoke the workflow on demand via `/issueflow-issue-*` and `@issueflow-version-bump` (#8).

## [0.1.4] - 2026-04-15

- New `issue-flow update` command and safer re-init messaging when a scaffold already exists (#5).
- Version bump plumbing (#6).

## [0.1.3] - 2026-04-15

- Packaging / metadata fix-up (no user-facing changes).

## [0.1.2] - 2026-04-15

- `/issue-init` can be run with no arguments: when the current branch matches `<N>-<slug>`, it offers to use issue `#N` (#3).

## [0.1.1] - 2026-04-04

- Ensure `.gitkeep` files are created in every `.issueflows/` subdirectory so empty folders are preserved in git.
- Project metadata polish and initial CI workflow for PyPI publishing.

## [0.1.0] - 2026-04-03

- Initial release: `issue-flow` CLI with `init`, Jinja2 templates for `/issue-init`, `/issue-start`, and `/issue-close` slash commands, and the `.issueflows/` directory scaffold.
