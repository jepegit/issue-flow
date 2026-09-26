# Status — Issue #392: workspace-wide cleanup

- [x] Done

Branch: `392-workspace-cleanup` (worktree `../issue-flow-392`)

## What's done

- Plan accepted with recommended answers (unique_work worktree → skip branch not
  member; `--apply` shipped in v1; `issueflows_only` dirt → classify + delete,
  skip switch/pull).
- `agent.classify_local_branches` extracted from `run_local_branches`
  (console-free; `agent local-branches` output unchanged).
- New `issue-flow workspace cleanup [--json] [--dry-run] [--no-fetch] [--apply]
  [--yes-delete-squash-landed] [--extra-root …]` (`agent.run_workspace_cleanup`,
  `cli.workspace_cleanup`). Classify-only default; per-member gate (no origin /
  detached / mixed-dirty / locked → skipped, loop continues); `default-sync`;
  five buckets; linked worktrees with bucket; A1/A2 plan with `recover` lines;
  `--apply` runs A1, `--yes-delete-squash-landed` adds A2 with `<name> <tip>
  <flag>` in `applied`. Non-ff members never pulled. `unique_work` never planned.
- `gitutils.has_remote`, `gitutils.is_detached_head`.
- Skill + command templates: workspace-mode Input paragraph, step 4b (survey →
  one A1 confirm → one A2 confirm → optional B), step 10 "unless invoked with
  `all`", constraint on when `--apply` flags may be passed. Rules body and
  workflow-doc template mention `all`.
- Docs: `docs/cli.md` (table, synopsis, section), `docs/how-to/workspaces.md`,
  `docs/how-to/after-squash-merge.md`; design doc
  `multi-repo-workspaces.md` Phase 4c.
- Tests: `tests/test_workspace_cleanup.py` (16, real git repos: AC1 bucket
  parity, AC3 non-ff skip, AC4 unique_work, refusals, issueflows-only dirt,
  unique_work worktree, extra-root + locked, dry-run, apply A1 / A2, switch,
  never-pull), `test_cleanup_documents_workspace_mode` in `test_templating.py`.
- `uv run pytest` 952 passed; ruff check + format clean.
- `issue-flow update .` re-rendered `.cursor/` + `AGENTS.md` +
  `docs/issue-workflow.md` (also fixes the 0.5.15 → 0.5.16 skill stamp drift).

- Close: version 0.5.16 → 0.5.17 (`uv version --bump patch`), HISTORY.md
  promoted to `[0.5.17]`, test-registry rows added; essential suite green.

## Remaining work

- None. `graphify update .` intentionally not run (off-path per AGENTS.md).
