# Cursor issue workflow (slash commands)

This repo uses three Cursor **slash commands** under `.cursor/commands/` that line up with how we track GitHub issues in `.issueflows/01-current-issues/`. Use them in order when you pick up work from GitHub and want the assistant to follow the same steps.

| Command | File | Role |
|--------|------|------|
| `/issue-init` | `issue-init.md` | Pull an issue from GitHub into the repo as a local markdown file and tidy older current issues. |
| `/issue-start` | `issue-start.md` | Plan and implement the work described in `.issueflows/01-current-issues/`. |
| `/issue-close` | `issue-close.md` | Finish: tests, issue-folder housekeeping, commit, push, PR. |

---

## Agent Skills (optional)

`issue-flow init` / `issue-flow update` also install **Cursor Agent Skills** under `.cursor/skills/` — longer, on-demand playbooks that mirror the three commands:

| Skill folder | Invoke (examples) | Role |
|--------------|-------------------|------|
| `issueflow-issue-init` | `/issueflow-issue-init` or attach `@issueflow-issue-init` | Same flow as `/issue-init` (resolve reference, `gh`, archive, write `*_original.md`). |
| `issueflow-issue-start` | `/issueflow-issue-start` | Plan + confirmation + scope + implement from `.issueflows/01-current-issues/`. |
| `issueflow-issue-close` | `/issueflow-issue-close` | Tests, status checkboxes, move issue docs, commit, push, PR. |

Each skill sets `disable-model-invocation: true` so it is included when you **explicitly** invoke it, not on every chat. See [Agent Skills](https://cursor.com/docs/context/skills) in the Cursor docs.

---

## 1. `/issue-init` — capture the issue locally

**When:** You have a GitHub issue you want to work on (or archive older "current" issues before starting a new one).

**What you pass:** Either an issue number (e.g. `42`), a full GitHub issue URL, or nothing after `/issue-init`—in that case, on a branch named like `42-short-description`, the assistant may ask to use `#42` from the branch (and refuses to guess on `main`/`master`). The assistant resolves `owner/repo` from `git remote origin` when you only pass a number.

**What happens:**

- The assistant uses **GitHub CLI** (`gh`) to fetch title, body, URL, and number. You need `gh` authenticated (`gh auth login` if needed).
- It creates **`.issueflows/01-current-issues/issue<number>_original.md`** with the title, source URL, and the **exact** issue body from GitHub.
- **Archive:** Other files already in `.issueflows/01-current-issues/` (grouped by issue number, e.g. `issue121_*`) may be **moved** to `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, based on whether a status file for that issue contains a checked **Done** line (`- [x] Done`). The new issue's files are never moved as part of this step.
- If the target `issue<number>_original.md` already exists, the assistant should not overwrite it without asking.

**Result:** One canonical "original issue" file under `.issueflows/01-current-issues/` plus optional archive moves. You can add or edit a separate `issue<number>_status.md` (or similar) by hand or with the assistant as work progresses.

---

## 2. `/issue-start` — plan and implement

**When:** The issue is represented in `.issueflows/01-current-issues/` (at minimum the `*_original.md` file) and you are ready to code.

**What you pass:** Optional extra instructions (scope, constraints, design preferences).

**What the assistant does:**

1. Confirms **which** issue file applies if several exist or things are ambiguous.
2. **Plans** the work. If you are not in plan mode, it should stop and ask you to confirm before large changes.
3. Checks the plan is **not too broad**; may suggest splitting into smaller chunks.
4. **Implements** the plan (code, tests, and updates to issue status docs as appropriate for the task).

**Result:** Implementation aligned with the markdown in `.issueflows/01-current-issues/` and project rules (tests with `uv run`, dependency management with `uv`, etc.).

---

## 3. `/issue-close` — land the work

**When:** Implementation is done and you want to ship (commit, push, PR).

**What you pass:** Optional notes (branch name, PR title, draft PR, or "skip issue doc update").

**Typical steps the assistant follows:**

1. **Sanity check** — e.g. `uv run pytest`, review the diff.
2. **Issue folders** — update status markdown; use `- [x] Done` only when fully resolved. Move completed issue files from `.issueflows/01-current-issues/` to `.issueflows/03-solved-issues/`, or partly done work to `.issueflows/02-partly-solved-issues/` (see project rules).
3. **Commit** — focused staging and a clear message.
4. **Push** — to your usual remote (e.g. `origin`).
5. **Pull request** — open against the default branch; link the GitHub issue (`Closes #n` / `Refs #n`).
6. **After review** — address comments, merge when ready.

**Result:** Short summary of commit, push, and PR link (or what is blocked).

---

## End-to-end flow

```text
GitHub issue
    │  /issue-init
    ▼
.issueflows/01-current-issues/issueN_original.md  (+ optional status files)
    │  /issue-start
    ▼
Code + tests (+ status updates during work)
    │  /issue-close
    ▼
Commit → push → PR → merge
    │
    └── issue docs in .issueflows/03-solved-issues/ or .issueflows/02-partly-solved-issues/ when appropriate
```

The command definitions are the source of truth: `.cursor/commands/issue-init.md`, `issue-start.md`, and `issue-close.md`. The skill packages under `.cursor/skills/` repeat the same workflows for explicit invocation. This document is a readable overview only.
