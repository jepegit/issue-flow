# Issue #39: Expand issue-flow workflow with additional slash commands

Source: https://github.com/jepegit/issue-flow/issues/39

## Original issue text

## Description
The current **Init → Start → Close** workflow is a great foundation. However, to reduce friction during complex tasks, context switching, and post-merge cleanup, we should introduce a more granular set of commands.

## Proposed New Commands

### 1. `/issue-plan`
**Role:** Formalize the "thinking" phase before any code is touched.
* **Logic:** Move the planning steps currently in `/issue-start` into this dedicated command.
* **Output:** Generate an `issue<N>_plan.md` file and require explicit user confirmation before moving to implementation.

### 2. `/issue-pause`
**Role:** Safely park work to switch context.
* **Logic:**
  * Update the status file with "Remaining work".
  * Immediately move the issue group to `.issueflows/02-partly-solved-issues/`.
  * Suggest a WIP commit or switch the user back to the default branch (`main`/`master`).

### 3. `/issue-cleanup`
**Role:** Dedicated "janitor" for post-merge maintenance.
* **Logic:** * Extract the post-merge logic from `/issue-close` (Step 7).
  * Detect merged PRs via `gh pr view`.
  * Perform the "consolidated confirm" to delete local branches whose tips are reachable from the default branch.

### 4. `/issue-yolo` (or `/issue-fast`)
**Role:** An "all-in-one" command for minor bugfixes and documentation.
* **Logic:** Chained execution of `init` -> `start` -> `implement` -> `close` in a single flow.
* **Safeguards:** * Must abort if tests (e.g., `uv run pytest`) fail.
  * Refuse to run if the working tree is dirty with unrelated changes.
  * Single confirmation at the start before performing automated commit/push/PR.

## Implementation Tasks
- [ ] Create Jinja2 templates for `/issue-plan.md.j2`.
- [ ] Create Jinja2 templates for `/issue-pause.md.j2`.
- [ ] Create Jinja2 templates for `/issue-cleanup.md.j2`.
- [ ] Create Jinja2 templates for `/issue-yolo.md.j2`.
- [ ] Update `cursor-issue-workflow.md` to reflect the expanded lifecycle.
- [ ] Update Agent Skills to include these new playbooks.

## Expected End-to-End Flow
1. **`/issue-init`**: Capture.
2. **`/issue-plan`**: Define approach.
3. **`/issue-start`**: Execute implementation.
4. **`/issue-pause`**: (Optional) Park work.
5. **`/issue-close`**: Land work.
6. **`/issue-cleanup`**: Final branch/folder hygiene.
