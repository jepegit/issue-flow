---
name: issueflow-issue-close
description: >-
  Run the /issue-close workflow: verify tests, optional uv semver bump, update
  issue status and folder locations, commit, push, and open a PR with a clear summary.
disable-model-invocation: true
---

# issue-flow — issue close (`/issue-close`)

Follow this skill when the user wants to **finish and land** work: tests, optional version bump, issue-folder updates, git, and PR. Match `.cursor/commands/issue-close.md`.

## When to use

- The user runs `/issue-close`, mentions **issue-close**, or asks to commit, push, or open a PR after issue-flow work.

## Optional version bump (command input)

If the user included text after `/issue-close` that requests a version bump:

- **`bump`** or **`patch`** → `uv version --bump patch`
- **`bump minor`** or **`minor`** → `uv version --bump minor`
- **`bump major`** or **`major`** → `uv version --bump major`
- Otherwise infer **patch** / **minor** / **major** from natural language; ask once if ambiguous.

When a bump applies: read `.cursor/skills/issueflow-version-bump/SKILL.md`, run the bump from the **project root** **after** the sanity check and **before** issue-folder updates and **before** commit / push / PR.

## Instructions

1. **Sanity check** — Run the project test suite (e.g. `uv run pytest`) and any checks the repo relies on. Skim the diff; avoid bundling unrelated changes.

2. **Optional version bump** — If the user asked for a bump (see above), follow `.cursor/skills/issueflow-version-bump/SKILL.md` and run `uv version --bump <patch|minor|major>`. If there is no bumpable `pyproject.toml`, skip and continue.

3. **Issue tracking** — Under `.issueflows/01-current-issues/`, update the status file: remaining work, checklists, and **`- [x] Done`** only when the issue is fully resolved. If fully resolved, move that issue’s markdown files (`issue<n>_*`) to `.issueflows/03-solved-issues/`. If partially resolved, move to `.issueflows/02-partly-solved-issues/`. Follow any stricter rules in `.cursor/rules/issueflow-rules.mdc` if present.

4. **Commit** — First check `git status`; if there are unrelated uncommitted changes, surface them and ask the user whether to include them — do not auto-include or drop silently. Then stage intentionally (include `pyproject.toml` and `uv.lock` if changed after a bump); write a commit message in full sentences describing what changed and why.

5. **Branch hygiene before push** — Run `git fetch --prune`, then sync with the default branch using `git pull --ff-only` (rebase or merge per project preference). Use `--ff-only` so unrelated history never gets pulled in silently; if it refuses, stop and ask how to reconcile. Resolve merge conflicts before pushing.

6. **Push** — Push to the remote the project uses (typically `origin`).

7. **Pull request** — Open (or update) a PR against the default branch. Body should explain the change, how to test, and link the GitHub issue (`Closes #n` / `Refs #n`).

8. **Post-merge branch cleanup** — Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Detect merge status with `gh pr view <branch> --json state,mergedAt,mergeCommit,headRefName`. If `gh` is unavailable, approximate with `git fetch --prune` + `git cherry origin/<default> <branch>` (all commits marked `-` means squash-merged).
   - **If merged:** ask once whether to run the standard cleanup. On yes: `git switch <default> && git pull --ff-only && git fetch --prune`. Then list every local branch whose tip is already reachable from `origin/<default>` (including squash-merged ones) and ask **once** (one consolidated yes/no listing every branch) before running `git branch -d <branch>` for each. Never use `-D` automatically; if `-d` refuses, report the branch and leave it alone.
   - **If not yet merged:** remind the user the working copy is still on the issue branch (not the default). Suggest `git switch <default>` before starting unrelated work, and tell them to re-run `/issue-close` after the PR merges so the post-merge cleanup runs.

9. **Output** — Summarize commit, push result, PR URL, and (when applicable) which local branches were deleted during post-merge cleanup. If blocked, report the next step.

## Constraints

- Do not skip failing tests without the user’s explicit agreement.
- Prefer focused commits; do not rewrite unrelated history unless asked.
