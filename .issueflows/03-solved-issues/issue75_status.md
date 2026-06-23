# Status for Issue #75: Iterative small fixes

This is an interactive `/iflow-fix` session. Each small fix gets a short plan,
is implemented only on confirmation, and is recorded below as a dated bullet.
The session is landed together via `/iflow-close`.

## Remaining work

- [x] Done

Session landed via `/iflow-close` (PR opened). All fixes recorded below.

## Iterative fixes log

- 2026-06-23 — `AGENTS.md`: aligned the manual section with the new `iflow-*`
  naming. Renamed two stale slash-command references: `/issue-close` →
  `/iflow-close` (config table) and `/issue-cleanup` → `/iflow-cleanup`
  (Conventions & gotchas). Left the managed (auto-generated) block untouched.
- 2026-06-23 — `README.md` + docs: aligned naming with the `iflow-*` scheme.
  `README.md` scaffold listing `issue-pause.md` → `iflow-pause.md`. Fixed the
  "File" column and one stale skill row in the docs workflow **template**
  (`src/issue_flow/templates/docs/issue-workflow.md.j2`) and mirrored the same
  fixes into the generated `docs/issue-workflow.md` (`issue-*.md` → `iflow-*.md`
  filenames, `graphify.md` → `iflow-graphify.md`, and skill
  `issueflow-issue-cleanup` → `iflow-cleanup`). Deleted the obsolete orphan
  `docs/cursor-issue-workflow.md` (no longer generated; the generator now writes
  `docs/issue-workflow.md`). `docs/developing.md` needed no changes. All 147
  tests pass.
