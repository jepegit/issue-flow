# Smart dispatcher for the issue-flow lifecycle

`/iflow` inspects the state of the focus issue and **dispatches** to the next logical command in the linear lifecycle — `/iflow-init`, `/iflow-plan`, `/iflow-start`, or `/iflow-close`. It never does work those commands don't already do; it just picks the right one for you.

Off-path commands (`/iflow-pick`, `/iflow-pause`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-fix`, `/iflow-graphify`) are **not** auto-dispatched. Invoke them directly when you need them. (`/iflow-pick` is the front door *before* `/iflow-init` — use it when you have not chosen an issue yet. `/iflow-fix` runs an interactive iterative-fixes session; while one is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`.)

Long-lived design docs, design decisions, and project good-practices live under `.issueflows/04-designs-and-guides/`. The downstream commands (`/iflow-plan`, `/iflow-start`, `/iflow-close`) read from and add to that folder as they run; `/iflow` itself does not touch it.

## Input

Optional free-form text after the command. `/iflow` forwards the raw trailing text to whichever command it dispatches to. Examples:

- `/iflow` — dispatch with no extra args.
- `/iflow 42` — forwards `42` (useful when state resolves to `/iflow-init`).
- `/iflow bump minor` — forwards `bump minor` (meaningful when state resolves to `/iflow-close`; otherwise the downstream command will ignore or ask).
- `/iflow stick to the existing logger` — forwards the hint (useful when state resolves to `/iflow-plan` or `/iflow-start`).

## Steps

0. **Resolve the focus issue number `N`.**
   - Run `git branch --show-current`. If it matches `^(\d+)-.+`, the leading digits are the **authoritative** `N`.
   - List `issue<n>_*` groups in `.issueflows/01-current-issues/`, and also check `.issueflows/02-partly-solved-issues/` and `.issueflows/03-solved-issues/` for archived groups matching `N`.
   - Pick `N` using this precedence:
     1. **Branch-derived `N` wins**, regardless of whether a group for `N` exists in `01-current-issues/`. State A (dispatch `/iflow-init`) will simply apply when no `issue<N>_*` files are present yet. If `issue<N>_*` is archived under `02-partly-solved-issues/` or `03-solved-issues/`, warn the user that `/iflow-init`'s archived-issue guard will ask for an explicit confirmation before re-opening.
     2. Else if exactly one group exists in `01-current-issues/`, use that `N`.
     3. Else if there are **no** groups at all in `01-current-issues/` (and no branch-derived `N`), fall through to dispatch `/iflow-init` (state A); `/iflow-init` itself will ask for a number.
     4. Else (no branch-derived `N`, multiple groups in `01-current-issues/`), **stop** and ask the user which issue to act on. Do not guess.

1. **Detect state and choose the dispatch target.** In priority order:

   | State | Condition | Dispatch to | Reason to report |
   |-------|-----------|-------------|------------------|
   | A | No `issue<N>_original.md` for the focus issue (or no focus issue at all) | `/iflow-init` | "no `*_original.md` yet" |
   | B | `issue<N>_original.md` exists, no `issue<N>_plan.md` | `/iflow-plan` | "no plan file yet" |
   | C | Plan exists, and either no status file or the status file does **not** contain `- [x] Done` | `/iflow-start` | "plan is confirmed but status is not `- [x] Done`" |
   | D | Status file contains `- [x] Done` (case-insensitive on `done`) | `/iflow-close` | "status marks the issue `- [x] Done`" |

   Use the first row whose condition matches. Never dispatch to more than one command in a single `/iflow` run.

2. **Announce and dispatch.** Before running the downstream command, print one line explaining the decision, for example:

   ```
   /iflow -> /iflow-plan  (issue #42: no plan file yet)
   ```

   Then run the exact same logic as the chosen command (follow `.cursor/commands/<command>.md`), forwarding the user's trailing text verbatim. The downstream command keeps all its own checkpoints (plan confirmation in `/iflow-plan`, `/iflow-start`'s soft stop when the plan is missing, `/iflow-close`'s unrelated-changes prompt, etc.).

3. **Report.** Summary should include:
   - the focus issue number and how it was resolved (branch-derived / only group / user-specified)
   - which command was dispatched to and why
   - the downstream command's own output
   - a one-line hint when an **off-path** command is the natural next step, e.g.:
     - state **D** + PR likely merged → "after the PR merges, run `/iflow-cleanup`"
     - mid-stream context switch needed → "to park this work, run `/iflow-pause`"
     - tiny fix you want in one shot → "consider `/iflow-yolo` next time"
     - `graphify-out/GRAPH_REPORT.md` looks stale (large refactor, new modules) → "consider `/iflow-graphify` to refresh the graph"

## Constraints

- `/iflow` never skips a downstream command's own prompts. If the downstream step asks a question, surface it normally.
- `/iflow` never auto-dispatches to `/iflow-pick`, `/iflow-pause`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-fix`, or `/iflow-graphify`. Those are explicit choices only.
- If the focus issue cannot be resolved (multiple active issues, branch ambiguous), stop and ask. Do not pick one silently.
- Do not modify files beyond what the downstream command would normally modify. `/iflow` itself writes nothing.

## Example invocations

- `/iflow` on a fresh branch `42-fix-login` with no `issueflows` files yet
  -> dispatches to `/iflow-init` which infers `#42` from the branch.
- `/iflow` on branch `42-fix-login` while unrelated groups (`issue99_*`, `issue100_*`) still sit in `01-current-issues/`
  -> branch-derived `N=42` wins; dispatches to `/iflow-init` (state A) which captures #42 and archives the other groups per its own sweep.
- `/iflow` after `/iflow-init 42` has run and `issue42_original.md` exists, but there is no `issue42_plan.md` yet
  -> dispatches to `/iflow-plan`.
- `/iflow` after `/iflow-plan` has written and the user confirmed `issue42_plan.md`, with no `issue42_status.md` or an unchecked `- [ ] Done`
  -> dispatches to `/iflow-start`.
- `/iflow bump patch` after implementation is done and `issue42_status.md` contains `- [x] Done`
  -> dispatches to `/iflow-close bump patch`.
- `/iflow` on branch `99-partial-work` after the issue was paused (files now under `02-partly-solved-issues/`)
  -> branch-derived `N=99` wins; dispatches to `/iflow-init` (state A since `01-` has no `issue99_*`). `/iflow` warns up front that `/iflow-init`'s archived-issue guard will trigger and ask for explicit confirmation before restoring the group to `01-current-issues/`.
