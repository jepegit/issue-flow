# `/issue-fix`: interactive iterative-fix sessions

**Issue:** [#54 — Allow for more interactive sessions](https://github.com/jepegit/issue-flow/issues/54)
**Status:** decided 2026-06-16, implemented in the same issue.
**Scope:** a new off-path slash command (`/issue-fix`) + mirrored skill for
working a stream of small fixes on a single long-lived branch.

## Context

issue-flow's linear lifecycle (`/issue-init` → `/issue-plan` → `/issue-start` →
`/issue-close`) assumes one well-defined deliverable per issue. Issue #54 asked
for a lighter, interactive mode: a single branch where you fix one small thing,
use the code, find the next small thing, and so on — each fix getting a short
plan and an implementation only if the user wants it, with everything recorded
in the issue's markdown and landed together via `/issue-close`.

## Decisions

### 1. New off-path command, mirroring the existing command/skill pattern

`/issue-fix` ships as a `commands/issue-fix.md.j2` template **and** a mirrored
`skills/issueflow_issue_fix/SKILL.md.j2`, both registered in
`templating.py` (`COMMAND_NAMES`, `SKILL_DIRS`). It is **off-path** like
`/issue-pick`, `/issue-yolo`, and `/graphify`: `/iflow` never auto-dispatches to
it (it creates GitHub issues + branches and then drives an open-ended loop), and
the skill sets `disable-model-invocation: true`.

Manifest counts: cursor 25 → 27, codex 14 → 15 (skills 13 → 14).

### 2. Always create a GitHub issue (`gh`); no local-only mode in v1

Per the issue comment, setup always creates a real GitHub issue via
`gh issue create` (after showing the title/body and confirming). A local-only
mode was considered (work without a GitHub issue, e.g. offline) and deferred —
keeping a single, predictable setup path for v1. GitLab is **not** supported:
issue-flow's external surface is `git` + `gh` (GitHub).

### 3. Per-fix log lives in `issue<N>_status.md`

Each fix is appended as a dated bullet under an `## Iterative fixes log` section
in the existing `issue<N>_status.md`, rather than a dedicated
`issue<N>_fixes.md`. This keeps the issue group to the familiar
`_original` / `_status` shape and means the existing folder-sweep and
`- [ ] Done` / `- [x] Done` conventions keep working unchanged. The checkbox
stays unchecked for the whole session; `/issue-close` flips it when the work
lands.

### 4. Coexist with `/issue-pick fix` (do not merge)

`/issue-pick fix` already creates a new general-fixes issue + branch, but then
hands back to the normal `/issue-plan` → `/issue-start` flow (a one-shot setup).
`/issue-fix` instead **stays** and runs the iterative loop until
`/issue-close`. They overlap on setup but serve different intents, so they
coexist; the docs cross-reference each other rather than folding one into the
other.

### 5. Delegate, don't duplicate

Setup delegates local capture to the `/issue-init` flow (issue fetch +
`issue<N>_original.md` + archive sweep) and finishing to `/issue-close`
(tests, optional bump, status, commit, push, PR). `/issue-fix` only adds the
GitHub-issue creation, the branch-from-current-vs-default choice, the status
seed, and the fix loop on top.

### 6. `/iflow` interaction: document only

An active `/issue-fix` session has an `issue<N>_original.md` but intentionally no
`issue<N>_plan.md` (each fix uses a lightweight inline plan instead). A stray
`/iflow` would therefore see "no plan file yet" and dispatch `/issue-plan`. v1
handles this by **documentation** — `/iflow`, its skill, and the rules tell the
user to drive an active session with `/issue-fix` + `/issue-close`, not `/iflow`.
A status marker that `/iflow` could detect and decline on was considered and
deferred as unnecessary complexity for v1.

## Consequences

- Two new template files; manifest entry count rises by 2 (per editor with a
  `commands_dir`) / by 1 for command-less editors (Codex).
- Touch points updated everywhere commands are enumerated:
  `commands/iflow.md.j2`, `skills/issueflow_iflow/SKILL.md.j2`,
  `rules/_body.md.j2`, `docs/issue-workflow.md.j2`, `README.md`, and
  `tests/test_templating.py` (counts + expected command/skill membership + a
  focused `/issue-fix` test).

## Notes for future work

- A local-only session mode (`/issue-fix local <name>`) could be added if users
  want offline / no-GitHub buckets.
- If sessions become long, a status marker enabling `/iflow` to recognize and
  defer to an active `/issue-fix` session would remove the documentation-only
  caveat in decision 6.
