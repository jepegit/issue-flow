---
name: issueflow-issue-close
description: >-
  Run the /issue-close workflow: verify tests, update issue status and folder
  locations, commit, push, and open a PR with a clear summary.
disable-model-invocation: true
---

# issue-flow — issue close (`/issue-close`)

Follow this skill when the user wants to **finish and land** work: tests, issue-folder updates, git, and PR. Match `.cursor/commands/issue-close.md`.

## When to use

- The user runs `/issue-close`, mentions **issue-close**, or asks to commit, push, or open a PR after issue-flow work.

## Instructions

1. **Sanity check** — Run the project test suite (e.g. `uv run pytest`) and any checks the repo relies on. Skim the diff; avoid bundling unrelated changes.

2. **Issue tracking** — Under `.issueflows/01-current-issues/`, update the status file: remaining work, checklists, and **`- [x] Done`** only when the issue is fully resolved. If fully resolved, move that issue’s markdown files (`issue<n>_*`) to `.issueflows/03-solved-issues/`. If partially resolved, move to `.issueflows/02-partly-solved-issues/`. Follow any stricter rules in `.cursor/rules/issueflow-rules.mdc` if present.

3. **Commit** — Stage intentionally; write a commit message in full sentences describing what changed and why.

4. **Branch hygiene** — Ensure the branch is up to date with the default branch where appropriate; resolve merge conflicts before pushing.

5. **Push** — Push to the remote the project uses (typically `origin`).

6. **Pull request** — Open (or update) a PR against the default branch. Body should explain the change, how to test, and link the GitHub issue (`Closes #n` / `Refs #n`).

7. **Output** — Summarize commit, push result, and PR URL, or the next blocker.

## Constraints

- Do not skip failing tests without the user’s explicit agreement.
- Prefer focused commits; do not rewrite unrelated history unless asked.
