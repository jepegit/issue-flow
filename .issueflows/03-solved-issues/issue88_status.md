# Status — Issue #88: enhance issue-flow cli tool for agentic use

## Summary

Promoted the most-repeated, deterministic lifecycle mechanics into real
`issue-flow` subcommands (1 top-level + 4 under an `agent` sub-app = 5 new
commands), and taught the high-value skills/commands to prefer them with a
graceful manual fallback (the CLI is optional — only present when the user
installs `issue-flow`).

## What landed

- **`src/issue_flow/tracking.py`** — first Python reader of `.issueflows/`:
  issue-group parsing, `- [x] Done` checkbox rule, lifecycle stage, focus
  resolution, and sweep planning/applying.
- **`src/issue_flow/gitutils.py`** — best-effort `git`/`gh` wrappers
  (`shutil.which` -> argv -> `subprocess.run(check=False)`), returning `None`
  when a tool is missing: current/default branch, clean/dirty, ahead/behind,
  `owner/repo` parse (HTTPS+SSH), `gh issue view`/`list`.
- **`src/issue_flow/agent.py`** — orchestrators for `status`, `agent state`,
  `agent preflight`, `agent sweep`, `agent capture` (text + `--json`, graceful
  degradation).
- **`src/issue_flow/cli.py`** — top-level `status` command + `agent` Typer
  sub-app (`state`/`preflight`/`sweep`/`capture`).
- **Templates** — added an optional "CLI fast path" note (with manual
  fallback) to `iflow`, `iflow-status`, `iflow-init`, `iflow-start`,
  `iflow-plan` (both command and skill variants).
- **Docs/version** — README documents the new commands and drops `status`
  from Future plans; `__init__.py` `__version__` synced to `0.4.1a3`.
- **Tests** — new `test_tracking.py`, `test_gitutils.py`, CLI smoke/JSON tests
  in `test_cli.py`, and template fast-path assertions in `test_templating.py`.

## Close actions (#88)

- Added a durable design note: `.issueflows/04-designs-and-guides/agentic-cli.md`.
- Added a `## [Unreleased]` entry to `HISTORY.md` (no version bump requested).
- Hardened text output: `rich.markup.escape()` on untrusted titles/branch names
  (+ regression test `test_status_text_escapes_malicious_title`).

## Verification

- `uv run pytest` — 240 passed.
- `uv run ruff check src/ tests/` — clean.
- Manual smoke against this repo: `status`, `agent state --json`,
  `agent preflight --json`, `agent sweep --dry-run`, `status --json` (GitHub
  cross-ref) all behave as expected.

## Remaining / follow-ups (out of scope for this PR)

- Other lifecycle commands (`/iflow-cleanup` branch deletion, `HISTORY.md`
  append) could be promoted later; left agent-side for now.
- This repo's own rendered `.cursor/` scaffold reflects the template changes
  only after `issue-flow update` is run (templates are the source of truth).

- [x] Done
