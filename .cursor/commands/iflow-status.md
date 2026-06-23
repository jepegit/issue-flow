# Status overview of the repository's issues (`/iflow-status`)

`/iflow-status` prints a **read-only** snapshot of where every issue stands —
both the local issue-flow tracking state under `.issueflows/` (focus,
parked, solved) and the open issues on GitHub. It answers "where do all my
issues stand right now?" at a glance. Unlike `/iflow` (which *acts* on the single
focus issue), `/iflow-status` only reports and never changes anything.

This is an **off-path** command — the lifecycle dispatcher (`/iflow`) never
auto-runs it. Invoke it explicitly whenever you want a bird's-eye view.

## Input

Optional free-form text after the command:

- **No extra text** — full report (local tracking + GitHub).
- **`local`** — skip the GitHub query; report only the `.issueflows/` state.
- **A hint** (e.g. `milestone v0.4`, `bugs`) — bias the GitHub section toward
  matching issues (best-effort filter; still read-only).

## Steps

1. **Context / preflight** (read-only; no `fetch` is required, but a `git fetch --prune` keeps ahead/behind accurate).
   - Detect the default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else `main`.
   - Report current branch, clean/dirty working tree (`git status --porcelain`), and ahead/behind vs `origin/<default>` (`git rev-list --left-right --count origin/<default>...HEAD`).
   - If the branch matches `^(\d+)-.+`, treat the leading digits as the focus issue number `N`.

2. **Focus issue** (`.issueflows/01-current-issues/`).
   - List `issue<n>_*` groups present. Normally there is exactly one (the focus issue); if the branch gave an `N`, prefer that group.
   - For the focus group, read the title from `issue<n>_original.md` and classify its **lifecycle stage** using the same file-presence logic as `/iflow` (first match wins):
     - **init** — no `issue<n>_original.md` yet → next step `/iflow-init`.
     - **plan** — original exists, no `issue<n>_plan.md` → next step `/iflow-plan`.
     - **start** — plan exists, status file missing or its `- [x] Done` is unchecked → next step `/iflow-start`.
     - **close** — a status file contains `- [x] Done` (case-insensitive on `done`) → next step `/iflow-close`.
   - Show the stage and the suggested next step.

3. **Parked work** (`.issueflows/02-partly-solved-issues/`).
   - List each `issue<n>_*` group: number, title (from `issue<n>_original.md`), and a one-line status if a status file exists. These are started-but-unfinished issues worth resuming (`/iflow-pick` surfaces them first).

4. **Solved archive** (`.issueflows/03-solved-issues/`).
   - Report the count of distinct solved issue numbers and list the most recent few (by issue number) so the section stays terse.

5. **Open GitHub issues** (skip entirely if input was `local`).
   - Run `gh issue list --state open --json number,title,labels,milestone,updatedAt` (add `--repo owner/repo` if the default remote is ambiguous). Apply any input hint as a best-effort filter on title/labels/milestone.
   - Cross-reference each open issue against the local folders and tag its **local state**:
     - **focus** — matches the focus issue in `01-current-issues/`.
     - **parked** — a group exists under `02-partly-solved-issues/`.
     - **solved-locally** — a group exists under `03-solved-issues/` (open on GitHub but archived locally — may need closing on GitHub).
     - **untracked** — no local group yet (candidate for `/iflow-pick`).
   - If `gh` is missing or unauthenticated, **do not fail**: skip this section and note that GitHub data was unavailable (suggest `gh auth login`).

6. **Summary line.** One line, e.g. `Focus: #20 (start). Parked: 2. Solved: 31. Open on GitHub: 7 (5 untracked).`

## Constraints

- **Read-only.** `/iflow-status` writes nothing, moves no files, and never creates branches, commits, or GitHub issues. It only reads `.issueflows/` and runs read-only `git` / `gh` queries.
- **Off-path.** Never auto-dispatch `/iflow-status` from `/iflow`, `/iflow-start`, or `/iflow-close`. The user opts in.
- **Degrade gracefully.** Missing `gh`, no network, or an empty `.issueflows/` must still produce a useful local report rather than an error.
- Do not run tests, package managers, or any command with side effects.

## Output to user

Present the report as short sections in this order: **Context**, **Focus issue**,
**Parked work**, **Solved archive**, **Open GitHub issues** (unless `local`), and
a final **Summary** line. Keep each entry to one line where possible. Note any
skipped section (e.g. GitHub skipped because `gh` was unavailable or `local` was
passed).

## Example invocations

- `/iflow-status` — full report (local tracking + open GitHub issues).
- `/iflow-status local` — local `.issueflows/` state only, no GitHub query.
- `/iflow-status milestone v0.4` — full report, GitHub section biased toward the `v0.4` milestone.
