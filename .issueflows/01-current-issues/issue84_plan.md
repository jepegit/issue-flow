# Issue #84 — plan: `iflow-archive` (archive solved issueflow files)

## Goal

Add an `iflow-archive` workflow surface (skill + slash command) that condenses
selected `issue<N>_*` groups from `.issueflows/03-solved-issues/` into a single
dated `YYYY-MM-DD_archived_issues.md` summary file, records a git ref for
recovery, and removes the original files — plus an optional
`issue-flow agent archive` CLI fast path for the mechanical steps.

## Constraints

- Templates are the source of truth: new surfaces live under
  `src/issue_flow/templates/` (`commands/iflow-archive.md.j2`,
  `skills/iflow_archive/SKILL.md.j2`); this repo's own `.cursor/` copies get
  refreshed via `issue-flow update` at the end.
- **CLI is optional, never assumed** (see
  `.issueflows/04-designs-and-guides/agentic-cli.md`): the skill must work
  standalone with manual steps; the CLI is only a fast path.
- **LLM judgment stays agent-side**: per-issue summarisation is interpretive
  and stays in the skill; only deterministic mechanics (candidate listing,
  file deletion, git ref capture) are promoted to the CLI.
- Off-path: never auto-dispatched by `/iflow`, `/iflow-start`, or
  `/iflow-close` — destructive, explicit-only, one consolidated confirm.
- Archive requires a **clean working tree** and ends with a commit offer, so
  the recorded git ref actually guarantees recoverability.
- The archive file must NOT match `^issue(\d+)_` so `tracking.group_issue_files`
  keeps ignoring it (dated prefix guarantees this).

### Prior art

- `tracking.plan_sweep` / `apply_sweep` + `SweepMove` — mirror as
  `plan_archive` / `apply_archive` + `ArchiveMove` (plan/apply split,
  `--dry-run` previewability).
- `agent.run_sweep` — mirror as `run_archive` (exit-code + text/`--json`
  contract, graceful degradation).
- `gitutils` best-effort wrappers — add a `head_sha()` helper
  (`git rev-parse HEAD`) following the same `None`-on-missing pattern.
- Skill/command template pairs, e.g. `skills/iflow_status/SKILL.md.j2` +
  `commands/iflow-status.md.j2` — structure, frontmatter, "CLI fast path"
  callout, off-path constraints wording.
- Registration points: `templating.py` (`COMMAND_NAMES`, `SKILL_DIRS`),
  `modes.toml`, `rules/_body.md.j2`, `docs/issue-workflow.md.j2`
  (tests in `test_templating.py` / `test_modes.py` iterate these lists).
- `.issueflows/00-tools/verify_scaffold.py` — reusable end-to-end render check.

## Approach

**Workflow (encoded in the skill/command templates):**

1. **Preflight** — require a clean working tree (stop if dirty); capture
   `git rev-parse HEAD` as the pre-archive ref.
2. **Select** — list `issue<N>_*` groups in `03-solved-issues/` (number +
   title via the `# Issue #N: <title>` heading). Smart default: propose
   archiving everything **except the most recent K groups** (default K=5,
   "recent" = highest issue numbers); user can override with an explicit
   list, `all`, or a different K. One consolidated confirm showing exactly
   which issues get summarised + deleted.
3. **Summarise (agent-side)** — for each chosen issue read `_original` /
   `_plan` / `_status` and write a compact entry (number, title, GitHub link,
   2–4 sentence outcome summary) into
   `.issueflows/03-solved-issues/YYYY-MM-DD_archived_issues.md`. File header
   records the date, the pre-archive ref, the archived file list, and
   recovery instructions (`git show <ref>:<path>`, `git log -- <path>`).
   Same-day rerun appends a new section to the existing dated file.
4. **Delete** — remove the archived `issue<N>_*` files (mechanical; CLI fast
   path or manual `git rm`).
5. **Commit offer** — propose a single commit
   (`chore(iflow): archive N solved issues (pre-archive ref <short-sha>)`);
   respect "only commit when explicitly asked" by making it a confirm.

**CLI fast path:** `issue-flow agent archive --issues 1,2,3 [--dry-run]
[--json] [-C dir]` — plans/applies deletion of the named solved groups and
reports `head_sha`; refuses issues not found in the solved folder. It does
NOT write the summary file (that is agent judgment). Backed by
`tracking.plan_archive` / `apply_archive`.

## Files to touch

- `src/issue_flow/templates/skills/iflow_archive/SKILL.md.j2` — new skill (workflow above).
- `src/issue_flow/templates/commands/iflow-archive.md.j2` — new slash command.
- `src/issue_flow/templating.py` — add `iflow-archive` to `COMMAND_NAMES`, `iflow_archive` to `SKILL_DIRS`.
- `src/issue_flow/modes.toml` — add to the `simple` mode lists (pure-markdown lifecycle fits; `standard` = "all" picks it up automatically).
- `src/issue_flow/tracking.py` — `ArchiveMove`, `plan_archive`, `apply_archive`.
- `src/issue_flow/gitutils.py` — `head_sha()`.
- `src/issue_flow/agent.py` — `run_archive`.
- `src/issue_flow/cli.py` — `agent archive` subcommand.
- `src/issue_flow/templates/rules/_body.md.j2` — one-paragraph mention (off-path, destructive-with-confirm).
- `src/issue_flow/templates/docs/issue-workflow.md.j2` — command table row + section.
- `tests/test_tracking.py`, `tests/test_gitutils.py`, `tests/test_cli.py` — new unit tests; `test_templating.py` / `test_modes.py` cover registration via the shared lists.
- This repo's rendered `.cursor/` surfaces + managed `AGENTS.md` block — refreshed via `uv run issue-flow update . --skip-dep-check` at the end of `/iflow-start`.

## Test strategy

- `uv run pytest` — full suite incl. new tests (archive plan/apply semantics,
  `agent archive` exit codes / `--dry-run` / `--json`, `head_sha`).
- `uv run ruff check src/ tests/` — lint.
- `uv run .issueflows/00-tools/verify_scaffold.py` — end-to-end render check.
- Manual end-to-end: scaffold a throwaway project
  (`git init` + `uv run --project /workspace issue-flow init . --skip-dep-check`),
  seed fake solved issues, run `issue-flow agent archive --dry-run` and apply,
  verify deletion + recoverability via `git show <ref>:<path>`.

## Open questions

1. **CLI fast path in scope?** Recommended (mirrors the sweep precedent;
   deletion benefits from previewable determinism), but the issue only asks
   for the skill — say the word and it becomes a skill-only PR (drop
   `tracking`/`agent`/`cli`/`gitutils` changes).
2. **Selection default** — keep the most recent 5 solved groups unarchived
   ("recent" = highest issue number); OK, or prefer age-based (git mtime)?
3. **Simple mode** — include `iflow-archive` in the `simple` mode surface
   list (proposed yes: it is markdown-only and needs no `gh`)?
