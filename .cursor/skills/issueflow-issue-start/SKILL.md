---
name: issueflow-issue-start
description: >-
  Run the /issue-start workflow: pick the current issue markdown, plan (with
  confirmation when not in plan mode), guard scope, then implement with project
  conventions (e.g. uv run).
disable-model-invocation: true
---

# issue-flow — issue start (`/issue-start`)

Follow this skill when the user wants to **begin implementation** from issue notes, matching `.cursor/commands/issue-start.md` and project rules.

## When to use

- The user runs `/issue-start`, mentions **issue-start**, or asks to implement from `.issueflows/01-current-issues/`.
- Work should follow the issue-flow markdown workflow and stay aligned with `.cursor/rules/issueflow-rules.mdc` when present.

## Instructions

1. **Select the issue** — Read `.issueflows/01-current-issues/`. If there is no `*_original.md` (or multiple ambiguous groups), **stop** and ask which issue to use.

2. **Branch status preflight** (non-destructive) — Detect the default branch (prefer `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind counts vs `origin/<default>`. If on the default branch, propose creating an issue branch (`git switch -c <N>-<short-slug>`); ask before running. If the current branch matches `^(\d+)-.+` and files for that issue now live in `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, warn the branch looks stale and ask whether to switch back before continuing. If the branch is neither default nor an issue-style branch, warn and ask whether to continue. Never delete a branch from `/issue-start`.

3. **Sweep stale current issues** (auto-safe) — Group files in `.issueflows/01-current-issues/` by `issueNN_` prefix. For every group **other than the focus issue**, move the whole group to `.issueflows/03-solved-issues/` if any of its status files contains `- [x] Done` (case-insensitive on `done`), otherwise move it to `.issueflows/02-partly-solved-issues/`. Never move the focus issue's files. Report every move.

4. **Plan first** — Produce a concrete plan (steps, files touched, tests). If you are **not** in plan mode, **stop and ask for explicit confirmation** before implementing, per the command definition.

5. **Scope check** — If the plan is broad, propose splitting into phases and ask whether to narrow scope before coding.

6. **Implement** — Execute the confirmed plan. Prefer minimal, focused diffs. Match existing code style and tooling.

7. **Project conventions**
   - Run Python via **`uv run`** (scripts, pytest, tools), not bare `python`, unless the user overrides.
   - Manage dependencies with **`uv add` / `uv remove` / `uv sync`** only.
   - After meaningful progress, update or create a status markdown file under `.issueflows/01-current-issues/` (e.g. `issue<number>_status.md`) with an explicit **Done** checkbox: `- [ ] Done` until fully resolved, then `- [x] Done`.

8. **Reporting** — Summarize what changed, what remains, and where the issue docs live. Include any branch warnings from step 2 and any issue-group moves from step 3.

## Constraints

- Do not invent issue text; treat `*_original.md` as read-only source of requirements unless the user asks to edit it.
- The stale sweep in step 3 is the **only** automatic move `/issue-start` performs, and it never touches the focus issue's own files. Do not move the focus issue's files between `01-` / `02-` / `03-` folders during `/issue-start`.
- Never delete or force-update git branches from `/issue-start`.
