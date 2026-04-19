# History

This file tracks notable changes to **issue-flow** per release.

Format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Release tags live on GitHub: <https://github.com/jepegit/issue-flow/releases>.
Pre-0.2.2 entries are reconstructed from git history and PR titles and may be less precise
than the GitHub release notes they link to.

## [Unreleased]

- `issue-flow init` now creates or extends a project `.env` with `ISSUEFLOW_*` hints (#35).
- Rename `ISSUEFLOW_CURSOR_DIR` to the more tool-agnostic `ISSUEFLOW_AGENT_DIR` (#36).
- `/issue-close` flags unrelated uncommitted changes and reminds about the issue branch after the PR is opened (#37).
- Branch and folder hygiene added to `/issue-init`, `/issue-start`, and `/issue-close`: non-destructive preflight reporting of current branch, ahead/behind counts, and working-tree state; automatic sweep of stale entries in `.issueflows/01-current-issues/` based on the `- [x] Done` marker in status files (#38, addresses #31).

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
