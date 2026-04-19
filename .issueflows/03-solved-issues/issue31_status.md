# Issue #31 status — problems with branches and merging

Source issue: [.issueflows/01-current-issues/issue31_original.md](issue31_original.md)

## Summary of decision

Extend the existing three slash commands (`/issue-init`, `/issue-start`, `/issue-close`) and their matching skills with:

- A **branch status preflight** (fetch --prune, current branch, ahead/behind vs default, stale-branch warning) in all three commands.
- A **stale-current-issues sweep** in `/issue-start` (same auto-safe rule already used by `/issue-init`): any `issue<n>_*` group other than the focus issue is moved to `03-solved-issues/` if a status file contains `- [x] Done`, otherwise to `02-partly-solved-issues/`.
- A **post-merge branch cleanup** in `/issue-close`: detect merge via `gh pr view`, offer `git switch <default> && git pull --ff-only && git fetch --prune`, then ask once (one consolidated yes/no) before `git branch -d` on every local branch whose commits are already in the default branch (including squash-merged ones). `-D` is never used automatically.
- An **archived-issue guard** in `/issue-init` so re-opening an issue that already lives in `02-`/`03-` requires an extra confirmation.
- A short **Branch hygiene** and **Folder hygiene** section in the workspace rules so the assistant keeps these habits outside the three commands.
- Cleanup of the duplicated "Agent Skills (optional)" block in the workflow doc.

No new slash commands were added.

## Checklist

- [x] Add branch-preflight + stale-sweep steps to `src/issue_flow/templates/commands/issue-start.md.j2`.
- [x] Replace the post-PR reminder in `src/issue_flow/templates/commands/issue-close.md.j2` with explicit post-merge cleanup (detect merge, switch, pull --ff-only, fetch --prune, consolidated confirm before `git branch -d`).
- [x] Add branch-preflight + archived-issue guard to `src/issue_flow/templates/commands/issue-init.md.j2`.
- [x] Mirror the same additions in the three skill files under `src/issue_flow/templates/skills/`.
- [x] Update `src/issue_flow/templates/docs/cursor-issue-workflow.md.j2`: new "Branch and folder hygiene" section, per-command bullets updated, duplicated Agent Skills block removed.
- [x] Append "Branch hygiene" and "Folder hygiene" subsections to `src/issue_flow/templates/rules/issueflow-rules.mdc.j2`.
- [x] Re-render the project scaffold via `uv run scripts/update_issueflow_setup.py` so the live `.cursor/commands/`, `.cursor/skills/`, `.cursor/rules/`, and `docs/cursor-issue-workflow.md` pick up the new behavior.
- [x] Add regression assertions in `tests/test_templating.py` for the new headings; run full `uv run pytest` (35 passed).
- [x] Commit the template + doc + test changes on branch `31-problems-with-branches-and-merging`, push, and open a PR linking `Closes #31`.
- [x] Done

## Remaining work before closing

None. The implementation, tests, and documentation updates are complete. Once the PR is merged, re-running `/issue-close` will exercise the new post-merge cleanup end-to-end (switch to default, pull --ff-only, fetch --prune, single confirm before `git branch -d`).

## Files touched

- `src/issue_flow/templates/commands/issue-init.md.j2`
- `src/issue_flow/templates/commands/issue-start.md.j2`
- `src/issue_flow/templates/commands/issue-close.md.j2`
- `src/issue_flow/templates/skills/issueflow_issue_init/SKILL.md.j2`
- `src/issue_flow/templates/skills/issueflow_issue_start/SKILL.md.j2`
- `src/issue_flow/templates/skills/issueflow_issue_close/SKILL.md.j2`
- `src/issue_flow/templates/docs/cursor-issue-workflow.md.j2`
- `src/issue_flow/templates/rules/issueflow-rules.mdc.j2`
- `tests/test_templating.py` (added regression assertions)

Re-rendered (not manually edited): `.cursor/commands/*.md`, `.cursor/skills/**/SKILL.md`, `.cursor/rules/issueflow-rules.mdc`, `docs/cursor-issue-workflow.md`.
