# Interactive iterative-fix session (`/iflow-fix`)

`/iflow-fix` opens an **interactive working session** on a single long-lived branch for a stream of small, iterative fixes. You fix one small thing, use the code, find the next small thing, and so on — each fix gets a short plan and is implemented only if you want it, and every fix is recorded in the issue's markdown. Finish the whole session with `/iflow-close`.

Use it when you do **not** have one well-defined deliverable but a bucket of little improvements you want to knock out on one branch (small bug fixes, typos, chores, polish).

This is an **off-path** command — the lifecycle dispatcher (`/iflow`) never auto-runs it, because it creates GitHub issues and branches and then drives an open-ended loop. Invoke it explicitly. While a session is active, drive it with `/iflow-fix` (continue fixing) and `/iflow-close` (finish) — not `/iflow`.

## How it relates to other commands

- **`/issue-pick fix`** is a *one-shot* setup: it creates a general-fixes issue + branch and hands you back to the normal `/iflow-plan` → `/iflow-start` flow. `/iflow-fix` instead **stays** with you and runs the iterative loop until you close. They coexist; pick `/iflow-fix` when you want the ongoing session.
- **`/iflow-close`** ends an `/iflow-fix` session exactly like any other issue (tests, optional bump, status update, commit, push, PR).

## Input

Optional free-form text after the command — a short **proposed name** for the session (used for the issue title and branch slug). Examples:

- `/iflow-fix polish-cli-output` — name the session `polish-cli-output`.
- `/iflow-fix` — no name: default the slug to `iterative-small-fixes` (made unique by appending the new issue number, e.g. `iterative-small-fixes`/branch `<N>-iterative-small-fixes`).

After the session is set up, a bare `/iflow-fix <description>` (or just describing a fix in chat) means "run the next fix in this session".

## Phase 1 — set up the session (once)

Run this only when there is no active session for the current branch yet (no `issue<N>_original.md` matching the branch).

1. **Preflight.** Detect the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`; fall back to `git symbolic-ref --quiet --short refs/remotes/origin/HEAD | sed 's|^origin/||'`, else `main`). Run `git fetch --prune`. Report the current branch and whether the working tree is clean (`git status --porcelain`). If the tree is dirty with unrelated changes, ask the user to commit/stash first.

2. **Create the GitHub issue (always, with confirmation).** Show the proposed title and body, then create it with `gh issue create` (add `--repo owner/repo` if the default remote is ambiguous):
   - **Title** — from the proposed name (e.g. `Iterative fixes: polish-cli-output`), or a generic `Iterative small fixes` when no name was given.
   - **Body** — note this is an interactive iterative-fixes session opened via `/iflow-fix`; individual fixes are recorded in the issue's status markdown and landed together via `/iflow-close`.
   - Capture the returned **issue number `N`**. A fresh issue is created each time — existing open fixes issues are not reused.
   - Change the chat/agent tab title to `Issue <N> <short session name>`.

3. **Create the branch (with confirmation).** Build the slug from the proposed name (kebab-case), defaulting to `iterative-small-fixes`. The branch name is `<N>-<slug>`.
   - **On the default branch** → branch off it: `git switch -c <N>-<slug>`.
   - **On a non-default branch** → **ask** whether to branch from the **current** branch or from the **default** branch, then create `<N>-<slug>` accordingly.
   - Require a clean tree before switching; confirm a non-obvious slug.

4. **Capture locally.** Delegate to the `/iflow-init` flow for `<N>` (follow `.cursor/commands/iflow-init.md`): fetch the issue, write `.issueflows/01-current-issues/issue<N>_original.md`, and run its archive sweep on the other groups. Do not re-implement that logic here.

5. **Seed the status file.** Create `.issueflows/01-current-issues/issue<N>_status.md` with:
   - a short header noting this is an interactive `/iflow-fix` session,
   - an unchecked `- [ ] Done` checkbox (kept unchecked until `/iflow-close`),
   - an **`## Iterative fixes log`** section (initially empty) where each fix is appended as a dated bullet.

## Phase 2 — the fix loop (repeat)

Each time the user proposes a small fix (or runs `/iflow-fix <description>` during the session):

1. **Restate the fix** in one line so scope is clear.
2. **Short plan.** Write a brief inline plan — a few lines naming the intent and the file(s) to touch. Keep it proportional to a *small* fix; do not write a full `issue<N>_plan.md`.
3. **Ask to proceed.** Implement **only if the user confirms**. If they decline or want changes, revise the mini-plan or drop the fix.
4. **Implement** the confirmed fix. Keep changes focused on that one fix.
5. **Record it.** Append a dated bullet to the **`## Iterative fixes log`** in `issue<N>_status.md` summarizing what changed (and any follow-ups). Offer to update the log proactively; always update when asked.

If a proposed "fix" turns out to be a substantial feature or touches many unrelated areas, say so and suggest handling it as its own issue (`/iflow-init` → `/iflow-plan` → `/iflow-start`) rather than as a loop iteration.

## Phase 3 — finish

When the user is done fixing, tell them to run **`/iflow-close`** to land the session (tests, optional version bump, status update, commit, push, PR). Do **not** auto-run it. After the PR merges, remind them to run `/iflow-cleanup`.

## Constraints

- **Off-path.** Never auto-dispatch `/iflow-fix` from `/iflow`, `/iflow-start`, or `/iflow-close`. The user opts in.
- **Never create a GitHub issue or branch without explicit confirmation.** Show what will be created first.
- **GitHub only.** Session issues are created with `gh` (GitHub). GitLab is not supported.
- **Respect git safety norms.** Branch off the detected default (or the current branch when the user chooses), never force-push, never delete branches from this command.
- **Keep the status checkbox accurate.** Leave `- [ ] Done` unchecked during the session; `/iflow-close` flips it to `- [x] Done` when the work lands.
- **Delegate, don't duplicate.** Use `/iflow-init` for local capture and `/iflow-close` to finish, rather than re-implementing their logic here.
- One fix per loop iteration; implement only on explicit confirmation.

## Output to user

Report:
- the session issue number `N` and title created, and the repository used (`owner/repo`)
- the branch created (`<N>-<slug>`) and what it was branched from (default vs current)
- the files written (`issue<N>_original.md`, `issue<N>_status.md`)
- for each loop iteration: the fix applied and the log bullet recorded
- the reminder to finish with `/iflow-close`

## Example invocations

- `/iflow-fix polish-cli-output` — set up the session (issue + branch + files), then start taking fixes.
- `/iflow-fix` — set up a generic `iterative-small-fixes` session.
- `/iflow-fix tighten the error message in cli.py` — run the next fix in an active session.
