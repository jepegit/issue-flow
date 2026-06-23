# Pick the next issue to work on (`/iflow-pick`)

`/iflow-pick` is the **front door** to the issue-flow lifecycle: it helps you **choose** what to work on next, creates the right issue branch, runs `/iflow-init` for you, and hands off to the normal flow. Use it when you are on the default branch with nothing in progress and you want help deciding what to pick up.

This is an **off-path** command — the lifecycle dispatcher (`/iflow`) never auto-runs it, because it is interactive and can create GitHub issues and branches. Invoke it explicitly.

## Input

Optional free-form text after the command:

- **No extra text** — survey candidates and ask which to pick.
- **`fix`** — skip the survey and create a single new "general fixes" GitHub issue (small bug / typo / chore bucket), then work on it. A new issue is created **every time** `fix` is used.
- **A hint** (e.g. `milestone v0.4`, `something about templating`, `the docs ones`) — used to bias the candidate ranking in Phase 1.

## Phases

`/iflow-pick` runs in three phases. Stop and ask whenever a choice is ambiguous; never create a GitHub issue or branch without explicit confirmation.

### Phase 1 — choose the issue

0. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else `main`). Run `git fetch --prune`. Report the current branch and whether the working tree is clean (`git status --porcelain`).

1. **`fix` shortcut.** If the user passed `fix`, skip candidate selection: go straight to creating a new general-fixes issue (see step 4) and continue to Phase 2.

2. **Source the candidates** (in precedence order):
   - **Parked work first.** If `.issueflows/02-partly-solved-issues/` contains any `issue<n>_*` groups, list them as the **primary** candidates — these are already-started issues that deserve to be finished before new work begins. Show issue number, title (from each `issue<n>_original.md`), and a one-line status if a status file exists.
   - **Otherwise, pull from GitHub.** Run `gh issue list --state open --json number,title,labels,milestone,updatedAt` (add `--repo owner/repo` if the default remote is ambiguous). Drop any issue already captured locally under `.issueflows/01-current-issues/`, `02-partly-solved-issues/`, or `03-solved-issues/`.

3. **Rank by relevance and present a shortlist.** Rank candidates using, in combination:
   - **Milestone** — prefer issues on the nearest / active milestone (and honour any milestone hint in the input).
   - **Labels** — prefer labels that match recent work or any label hint in the input.
   - **Topical similarity** — bias toward issues whose title/labels resemble recently solved issues (skim `.issueflows/03-solved-issues/` and recent branch names) so related work clusters together.

   Present a short ranked shortlist (roughly 3–7 entries) as a numbered list with number, title, labels, and milestone, then **ask the user to confirm** the top pick or choose another. Always allow a free-form override (a different issue number, URL, or `fix`). Do not silently pick one.

4. **Create a `fix` issue (only when requested).** When the user passed `fix` (or explicitly asks for a general-fixes bucket): create a **new** GitHub issue with `gh issue create` (e.g. title `chore: general fixes`, body noting it is a catch-all for small fixes/typos/chores). Confirm the title/body with the user first. Record the returned issue number and use it as the chosen issue. A fresh issue is created each time — existing open general-fixes issues are **not** reused.

5. **Over-large issue (note only).** If the chosen issue looks too involved to land in one PR, **mention** that it could be broken into sub-issues and that automated breakdown is planned as a follow-up (Phase B of issue #63). Do **not** auto-create sub-issues in this version — either proceed with the whole issue or let the user pick a smaller one.

### Phase 2 — create the branch

1. **Require a clean tree.** Run `git status --porcelain`. If anything is uncommitted, **stop** and ask the user to commit or stash first. Do not branch on top of unrelated changes.

2. **Branch off the default.** Switch to the default branch and fast-forward if needed, then create the issue branch using GitHub's numeric convention `git switch -c <N>-<short-slug>` (leading issue number, then a short kebab-case slug derived from the title). Confirm the branch name with the user if the slug is non-obvious.

3. **Run `/iflow-init` automatically.** The issue number is now known, so follow the `.cursor/commands/iflow-init.md` playbook for `<N>` (fetch the issue + comments, write `.issueflows/01-current-issues/issue<N>_original.md`, run its archive sweep). Do not re-implement that logic here — delegate to it.

### Phase 3 — hand off to the standard flow

1. The issue is now captured on a fresh branch. **Ask the user whether to continue with `/iflow-plan`** next (the usual next step). Do **not** auto-run it — make the handoff explicit so the user stays in control.

## Constraints

- **Off-path.** Never auto-dispatch `/iflow-pick` from `/iflow`, `/iflow-start`, or `/iflow-close`. The user opts in.
- **Never create GitHub issues or branches without explicit confirmation.** Show what will be created first.
- **Respect git safety norms.** Branch off the detected default, never force-push, never delete branches from this command.
- **Phase B is out of scope** for this version: no automated sub-issue creation, no parking of generated siblings under `02-partly-solved-issues/`. `/iflow-pick` only *mentions* the option (tracked as a follow-up to issue #63).
- Delegate issue capture to `/iflow-init` rather than duplicating its fetch/archive logic.

## Output to user

Report:
- which source the candidate came from (parked work vs GitHub) and the ranked shortlist shown
- the chosen issue number and title (and, for `fix`, that a new general-fixes issue was created)
- the branch created (`<N>-<slug>`) and that `/iflow-init` ran (file path written)
- the handoff prompt result (whether the user wants `/iflow-plan` next)

## Example invocations

- `/iflow-pick` — survey parked + GitHub issues, show a ranked shortlist, confirm, branch, init, hand off.
- `/iflow-pick fix` — create a new `chore: general fixes` issue, branch, init, hand off.
- `/iflow-pick milestone v0.4` — bias the ranking toward the `v0.4` milestone before asking.
