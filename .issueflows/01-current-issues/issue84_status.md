# Issue #84 — status

- [x] Done

## What's done

- Issue captured (`issue84_original.md`) and plan confirmed (`issue84_plan.md`).
- New workflow surfaces: `src/issue_flow/templates/skills/iflow_archive/SKILL.md.j2`
  and `src/issue_flow/templates/commands/iflow-archive.md.j2` — clean-tree
  preflight, pre-archive `git rev-parse HEAD` ref, smart selection default
  (keep the 5 most recent solved groups; `keep <K>` / explicit list / `all`
  overrides), one consolidated confirm, agent-written dated
  `YYYY-MM-DD_archived_issues.md` summary with recovery instructions, gated
  deletion, commit offer. Off-path.
- CLI fast path: `issue-flow agent archive <N> ... [--dry-run] [--json]`
  (`tracking.plan_archive`/`apply_archive`, `gitutils.head_sha`,
  `agent.run_archive`, `cli.agent_archive`) — mechanical deletion only,
  refuses when a requested issue has no solved group; summarising stays
  agent-side per `agentic-cli.md`.
- Registered in `templating.py` (`SKILL_DIRS`/`COMMAND_NAMES`), `modes.toml`
  (`simple` list; `standard` = all), `rules/_body.md.j2`,
  `docs/issue-workflow.md.j2`, `/iflow`'s off-path list.
- Unit tests added (`test_tracking.py`, `test_gitutils.py`, `test_cli.py`,
  `test_templating.py`); manifest counts bumped 19→20 (cursor) / 18→19 (codex).
- This repo's rendered surfaces refreshed via `issue-flow update .`
  (`.cursor/skills/iflow-archive/`, `AGENTS.md` managed block,
  `docs/issue-workflow.md`).
- Verified: `uv run pytest` (318 passed), `uv run ruff check src/ tests/`,
  `verify_scaffold.py`, plus a manual end-to-end run in a throwaway project
  (dry-run, refusal on missing issue, apply, recovery via
  `git show <ref>:<path>`, dated file ignored by grouping).

## Remaining work

- None. Ready for `/iflow-close`.
