# History

This file tracks notable changes to **issue-flow** per release.

Format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Release tags live on GitHub: <https://github.com/jepegit/issue-flow/releases>.
Pre-0.2.2 entries are reconstructed from git history and PR titles and may be less precise
than the GitHub release notes they link to.

## [Unreleased]

- **BREAKING: Renamed all slash commands from `/issue-*` to `/iflow-*` (#71).** The entire command family is now consistent with the `/iflow` dispatcher as the namespace root: `/issue-pick` → `/iflow-pick`, `/issue-init` → `/iflow-init`, `/issue-plan` → `/iflow-plan`, `/issue-start` → `/iflow-start`, `/issue-pause` → `/iflow-pause`, `/issue-close` → `/iflow-close`, `/issue-cleanup` → `/iflow-cleanup`, `/issue-yolo` → `/iflow-yolo`, `/issue-fix` → `/iflow-fix`, `/issue-status` → `/iflow-status`, `/graphify` → `/iflow-graphify`. Skills renamed from `issueflow-issue-*` to `iflow-*` (removing redundancy), `issueflow-version-bump` → `iflow-version-bump`, `issueflow-history-update` → `iflow-history-update`, `issueflow-graphify` → `iflow-graphify`. Run `issue-flow update` to migrate existing projects; old command files and skill folders are automatically pruned with a summary message.
- **New `/iflow-status` overview command (#20).** A read-only, off-path command (plus matching `iflow-status` skill) that prints a snapshot of where every issue stands: the local tracking state under `.issueflows/` (focus issue with its lifecycle stage via the `/iflow` logic, parked work, solved archive) plus open GitHub issues cross-referenced against the local folders and tagged focus / parked / solved-locally / untracked. Supports `local` (skip the GitHub query) and a hint arg; degrades gracefully when `gh` is unavailable. It writes nothing, moves no files, and `/iflow` never auto-dispatches to it.
- **`issue-flow graphify` now loads the project `.env` (#70).** `run_build` loads `<project_root>/.env` (`override=False`) before shelling out, so LLM API keys defined there (`GEMINI_API_KEY`, etc.) reach the `graphify extract` subprocess — previously they were ignored on this code path and `extract` failed with "no LLM API key found". README updated to document putting the key in `.env`.
- **New `/iflow-fix` interactive iterative-fix command (#54).** An off-path command (plus matching `iflow-fix` skill) for working a stream of small fixes on one long-lived branch: it creates a GitHub issue + `<N>-slug` branch (branching off the default, or asking current-vs-default when already on a branch), then loops over many small fixes — each gets a short inline plan, is implemented only on confirmation, and is recorded as a dated bullet under an `## Iterative fixes log` in `issue<N>_status.md` — and ends with `/iflow-close`. Coexists with `/iflow-pick fix` (the one-shot setup); always creates the issue via `gh` (GitLab not supported); `/iflow` never auto-dispatches to it.
- **Editor-agnostic scaffolding (#62).** `issue-flow init` / `update` now take a repeatable `--editor` / `-e` flag (`cursor` (default), `claude`, `opencode`, `codex`, or `all`) so the workflow can be scaffolded for Claude Code, opencode, and Codex CLI in addition to Cursor. A new `EditorProfile` registry (`src/issue_flow/editors.py`) drives a single shared template tree: Agent Skills are the portable core (emitted for every editor) and `AGENTS.md` is the convergent rules file, written as a non-destructive marker-delimited managed block so a hand-maintained `AGENTS.md` is preserved. Slash commands are emitted only where supported (Codex has none; opencode uses singular `command/`), with `.cursor/rules/issueflow-rules.mdc` (Cursor) and `CLAUDE.md` (Claude) layered on top. The rules body now has a single source of truth (`templates/rules/_body.md.j2`), the workflow doc was renamed `docs/cursor-issue-workflow.md` → `docs/issue-workflow.md`, and "Cursor" wording was neutralized for non-Cursor outputs. New `ISSUEFLOW_EDITOR` env var (default `cursor`); `ISSUEFLOW_AGENT_DIR` still overrides the agent directory when set. graphify auto-registration stays Cursor-only. Default `editor=cursor` keeps existing installs unchanged apart from the doc rename and the added shared `AGENTS.md`.
- **Rules defer to the project's toolchain instead of mandating uv (#58).** The scaffolded rules body (`templates/rules/_body.md.j2`) now tells agents to follow whatever Python toolchain a project already documents, with explicit conda handling (run scripts and `pytest` inside the activated conda env) and uv kept as the default/example; the prescriptive `uv run` phrasing in the `issue-start`/`issue-plan` command + skill templates was softened to match.
- **Doc/naming alignment follow-ups for `/iflow-*` (#75).** Cleaned up stale `issue-*` / `issueflow-issue-*` references left after the command rename: fixed `/iflow-close` and `/iflow-cleanup` mentions in `AGENTS.md`, corrected the scaffold listing in `README.md`, and fixed the "File" column plus a skill row in the workflow doc template (`templates/docs/issue-workflow.md.j2`) and the generated `docs/issue-workflow.md`. Removed the obsolete `docs/cursor-issue-workflow.md` orphan (superseded by `docs/issue-workflow.md`).
- **Project brief scaffold (`this-project.md`) (#53).** `issue-flow init` and `issue-flow update` now create `.issueflows/04-designs-and-guides/this-project.md` when it is missing, giving agents and humans a durable hand-editable project summary for stack, commands, conventions, entry points, and known limitations. Existing briefs are preserved, including under `init --force`, and scaffolded rules/commands/skills now point agents at the brief when present.

## [0.3.2] - 2026-06-06

- **New `/issue-pick` front-door command (#63).** A pre-`/issue-init` command (plus matching `issueflow-issue-pick` skill) that helps choose the next issue: parked work in `02-partly-solved-issues/` first, otherwise open GitHub issues ranked by milestone, labels, and topical similarity to recently solved work; `fix` creates a new "general fixes" issue each time. It then requires a clean tree, creates the `<N>-slug` branch off the default, runs `/issue-init`, and asks before handing off to `/issue-plan`. Off-path — `/iflow` never auto-dispatches to it. Automated sub-issue breakdown of over-large issues is intentionally deferred to a follow-up (Phase B).
- **Rename `build` → `graphify` (#56).** The graph-rebuild surface is now `/graphify` (slash command), `issueflow-graphify` (skill), and `issue-flow graphify` (CLI subcommand) — the old `build` names are gone. Pure rename, no behavior change; internal helpers keep their "build the graph" names.
- `/issue-init` now renames the chat/agent tab to reflect the issue topic, on the form "Issue <number> <short description>" (e.g. "Issue 74 cell info"). (#55)
- **`/issue-plan` prior-art discovery (#57).** New step 1.75 checklist: optional graphify skim of `GRAPH_REPORT.md`, grep for adjacent helpers, record findings under `### Prior art` in plan Constraints (or note none found); strong overlaps become Open questions. `/issue-start` reads that sub-section before new modules; `/issue-yolo` may abbreviate to grep-only for trivial runs. Matching updates to the `issueflow-issue-plan` skill, workflow doc, and templating tests.
- `/issue-init` now fetches GitHub issue comments and writes a curated "Comments (curated summary)" section into `issue<N>_original.md` (later comments win over earlier ones). New `issueflow-issue-comments` skill documents the triage rules (three buckets, noise filtering, edge cases). (#45)
- **Optional graphify integration (#49).** New `issue-flow graphify` CLI and `/graphify` slash command (plus matching `/issueflow-graphify` skill) wrap the [graphify](https://graphify.net) CLI. `issue-flow init` / `update` auto-run `graphify cursor install` when `graphify` is on PATH and otherwise print install hints — including PATH-orphan detection that surfaces "found at `<path>` but not on PATH" when the user installed `graphifyy` but uv's bin directory has not been added to PATH yet. The scaffolded rules and `/issue-start` / `/issue-close` point agents at `graphify-out/GRAPH_REPORT.md` when present so they can navigate by graph instead of grepping. Graphify is treated like `git` / `gh` — install standalone with `uv tool install graphifyy`, no Python extra (an `[graphify]` extra or `uv tool install issue-flow --with graphifyy` would leave the `graphify` CLI off PATH).

## [0.2.3] - 2026-04-19

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
- **New `04-designs-and-guides/` folder (#26).** `.issueflows/04-designs-and-guides/` gives projects a durable home for long-lived design docs, design decisions, and agreed good-practices. `issue-flow init` creates it; `issue-flow update` recreates it only if missing and never overwrites user files inside it. The issueflow rule file documents its purpose, and `/issue-plan`, `/issue-start`, `/issue-close`, `/iflow`, and `/issue-yolo` now read from and/or contribute to the folder during issue work.

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
