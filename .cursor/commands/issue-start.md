# Start working with current issue

The issue should already be explained in a markdown file in `.issueflows/01-current-issues`.

## Input
If additional input is added, use that for further detailed guidance

## Steps

0. If the issue markdown file is not present, or it is ambiguous which one to select, ask. Could it be that the user has not run the /issue-init command?

0.5 **Branch status preflight** (non-destructive — report, do not delete).
   - Detect the default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. If `gh` is unavailable, use `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else fall back to `main`.
   - Run `git fetch --prune` so tracking info is fresh.
   - Report: current branch, clean/dirty working tree (`git status --porcelain`), and ahead/behind counts vs `origin/<default>` (`git rev-list --left-right --count origin/<default>...HEAD`).
   - Classify the current branch:
     - On default (`main`/`master`/etc.): propose switching to or creating an issue branch before implementing, e.g. `git switch -c <N>-<short-slug>` where `N` is the focus issue number. Ask before running.
     - Matches `^(\d+)-.+`: treat the leading digits as issue number `N`. Cross-check `.issueflows/01-current-issues/`, `.issueflows/02-partly-solved-issues/`, and `.issueflows/03-solved-issues/`. If `issueN_*` is already under `02-partly-solved-issues/` or `03-solved-issues/`, warn that the branch looks stale and ask whether to switch back to default before continuing. Never delete a branch from `/issue-start`.
     - Any other branch name: warn that the branch does not look like an issue branch and ask whether to continue on it.

0.6 **Sweep stale current issues** (auto-safe file moves — no destructive git).
   - Group files in `.issueflows/01-current-issues/` by issue number (`issueNN_*`).
   - For every group **other than the focus issue**:
     - If any status markdown for that group contains `- [x] Done` (case-insensitive on `done`), move the whole group to `.issueflows/03-solved-issues/`.
     - Otherwise, move the whole group to `.issueflows/02-partly-solved-issues/`.
   - Never move the focus issue's own files.
   - Report every move (source -> destination, grouped by issue number) in the opening summary.

1. Plan. If not in plan mode, stop and ask for a confirmation.

2. Check that the plan is not too broad. If too broad, ask if it should be split into several parts.

3. Implement the steps of the plan
