# Plan the current issue before any code is written

The issue should already be captured in `.issueflows/01-current-issues/issue<N>_original.md` (via `/iflow-init`). Use this command to write a structured plan and get explicit user confirmation **before** `/iflow-start` starts editing code.

## Input

Optional free-form text after the command. Examples:

- **No extra text** — plan the focus issue using the `*_original.md` alone.
- Short constraints / design hints (e.g. "stick to the existing logger", "split into two PRs") — incorporate into the plan.

## Steps

0. **Locate the focus issue.** In `.issueflows/01-current-issues/`, find the `issue<N>_original.md`. If there is none, or multiple ambiguous groups, **stop** and ask the user. Suggest running `/iflow-init` first.

0.5 **Branch status preflight** (non-destructive — report, do not delete).
   - Detect the default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. If `gh` is unavailable, fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else `main`.
   - Run `git fetch --prune`.
   - Report current branch, clean/dirty working tree (`git status --porcelain`), and ahead/behind counts vs `origin/<default>` (`git rev-list --left-right --count origin/<default>...HEAD`).
   - If on the default branch, note it and suggest creating an issue branch (`git switch -c <N>-<short-slug>`) — do **not** auto-run it. Planning itself does not require a branch switch.

1. **Read the issue.** Load `issue<N>_original.md` and any existing `issue<N>_status.md`. Do not rewrite them from this command.

1.5 **Consult existing designs / guides.** Skim `.issueflows/04-designs-and-guides/` for design docs, design decisions, or documented good practices that touch the area you're about to plan. When relevant docs exist, cite them in the plan so the approach stays consistent with prior decisions.

1.75 **Prior-art discovery.** Before drafting the plan:
   1. **Graph (optional).** If `graphify-out/GRAPH_REPORT.md` exists, skim it for **God Nodes**, **Communities**, and **Suggested Questions** whose names touch the affected area. Note the community numbers. If the file is absent, skip this sub-step (grep-only is fine).
   2. **Grep.** Search the codebase for sibling helpers / functions that already do something adjacent to the new work (e.g. existing `filter_*`, `remove_*`, `yank_*`, `add_*` helpers in the same domain, or names surfaced by the issue / graph).
   3. **Record in plan.** Capture findings in a **`### Prior art`** sub-section under **`## Constraints`** in `issue<N>_plan.md`. For each item, record:
      - what it is (function name + module),
      - what convention it follows (param shape, column names, units),
      - and how the new work will be *consistent* with it (mirror, coexist, or migrate later).
      If nothing relevant turns up, write one bullet: `- None found (grep + graph checked).`
   4. **Strong overlap.** If the new work overlaps strongly with prior art, raise this explicitly under **`## Open questions`** ("merge with X?" vs "coexist with X?") rather than silently picking one.

2. **Explore, then propose.** Do enough read-only research (search, read files, check existing tests) to design the change. Keep it proportional to the issue — small fix = short plan.

3. **Write `issue<N>_plan.md`** in `.issueflows/01-current-issues/` with these sections:

   ```markdown
   # Plan for issue #<N>: <title>

   ## Goal
   One or two sentences on the desired outcome.

   ## Constraints
   - Project rules, coding standards, back-compat, scope limits.

   ### Prior art
   - `helper_name` (`module.path`) — convention: …; new work: mirror | coexist | migrate later
   - None found (grep + graph checked).   <!-- when applicable -->

   ## Approach
   Concrete design: data flow, affected modules, ordering of steps.

   ## Files to touch
   - path/one.py — what changes
   - path/two.md.j2 — what changes

   ## Test strategy
   - Existing tests to re-run, using the project's documented test command (e.g. `uv run pytest`, or `pytest` inside the activated conda env)
   - New tests or manual checks

   ## Open questions
   - Anything that needs the user's call before coding.
   ```

   Keep it terse but specific. Link to files with markdown links when helpful. If the plan expects to **produce** a design doc / decision record under `.issueflows/04-designs-and-guides/`, call that out explicitly (e.g. in **Files to touch**) so `/iflow-start` knows to create it.

4. **Scope check.** If the plan is broad (many unrelated files, several independent deliverables, or mixes refactors with feature work), **propose splitting** into smaller issues or phased PRs and ask the user before continuing.

5. **Confirm with the user.** Present the plan and **stop**. Ask one of:
   - **Accept** — the plan is good; next run `/iflow-start` to implement it.
   - **Revise** — call out sections to change; update `issue<N>_plan.md` in place and re-confirm.
   - **Abort** — remove `issue<N>_plan.md` (with the user's OK) or leave it as a draft.

   Do **not** proceed to implementation from `/iflow-plan`. That belongs to `/iflow-start`.

6. **If `issue<N>_plan.md` already exists.** Do not overwrite silently. Ask whether to:
   - **Update in place** (replace after the user sees the new content).
   - **Keep both** (append a timestamped suffix like `issue<N>_plan.v2.md`).
   - **Leave as is**.

## Output

Report:
- path written (e.g. `.issueflows/01-current-issues/issue<N>_plan.md`)
- brief summary of the plan
- whether the user has confirmed, revised, or paused on it
- any branch preflight warnings

## Constraints

- Read-only on source code; `/iflow-plan` writes **only** the plan file under `.issueflows/01-current-issues/`.
- Do not move files between `01-` / `02-` / `03-` folders from `/iflow-plan`.
- Do not run tests or package managers; that is `/iflow-start` and `/iflow-close`.
