# Issue #25 status — improve the issue close functionality

Source: [issue25_original.md](./issue25_original.md) / https://github.com/jepegit/issue-flow/issues/25

## Goal

Enhance `/issue-close` so that:

1. If there are uncommitted changes that the agent judged **not relevant** to this issue, it surfaces them and asks the user whether to include them in the commit.
2. After opening the PR, the agent reminds the user that the working copy is still on the issue branch (not the default branch like `main`), so new work doesn't accidentally land on the issue branch.

## Work done

- [x] Updated source command template `src/issue_flow/templates/commands/issue-close.md.j2`:
  - Added a leading bullet to step 4 that runs `git status` and asks the user about unrelated changes.
  - Inserted a new step 7 "Branch reminder" and renumbered "After review" to step 8.
- [x] Mirrored the same edits into the active `.cursor/commands/issue-close.md`.
- [x] Updated source skill template `src/issue_flow/templates/skills/issueflow_issue_close/SKILL.md.j2`:
  - Extended step 4 **Commit** with the `git status` / unrelated-changes check.
  - Inserted new step 8 **Branch reminder** and renumbered **Output** to step 9.
- [x] Mirrored the same edits into the active `.cursor/skills/issueflow-issue-close/SKILL.md`.
- [x] Added `test_init_issue_close_documents_uncommitted_and_branch_reminder` in `tests/test_init.py` asserting `git status`, `not relevant`, and `issue branch` appear in the rendered `issue-close.md`.
- [x] Verified `uv run pytest` passes.

## Remaining work

- None.

## Status

- [x] Done
