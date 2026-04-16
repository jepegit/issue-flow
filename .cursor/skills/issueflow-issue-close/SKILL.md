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

4. **Commit** — Stage intentionally (include `pyproject.toml` and `uv.lock` if changed after a bump); write a commit message in full sentences describing what changed and why.

5. **Branch hygiene** — Ensure the branch is up to date with the default branch where appropriate; resolve merge conflicts before pushing.

6. **Push** — Push to the remote the project uses (typically `origin`).

7. **Pull request** — Open (or update) a PR against the default branch. Body should explain the change, how to test, and link the GitHub issue (`Closes #n` / `Refs #n`).

8. **Output** — Summarize commit, push result, and PR URL, or the next blocker.

## Constraints

- Do not skip failing tests without the user’s explicit agreement.
- Prefer focused commits; do not rewrite unrelated history unless asked.
