# Issue #386: iflow-drive stops at the first yolo:no issue and cannot resolve stacked-PR / squash conflicts; should carry through under the overnight confirm

Source: https://github.com/jepegit/issue-flow/issues/386

## Original issue text

## Context

Real run on `jepegit/cellpy`, epic #783 (Epic L, live/incremental), skills baked at `issue-flow-version: 0.4.2a4`, CLI 0.5.13. The user ran `/iflow-drive 783` expecting an overnight, hands-off run that would draft, publish, implement, merge, and clean up. What happened:

1. Drive → auto → cycle stopped **before implementing anything** on the first Stage-2 issue (#779) with `stop_reason: "Stage 2 queue is yolo: no. Cycle halted on #779 before implementation (public protocol, not a small change)."`. `#780`, `#164`, `#781`, `#782` were never reached. The `drive_status.md` / `auto_status.md` files record this.
2. A human-driven session then had to do the rest: capture → plan → build → close for four issues, open four **stacked** PRs (#1101 → #1102 → #1103 → #1104, each based on the previous branch because the issues declared `Depends on`), then, after the first two squash-merged, hand-resolve the resulting `CONFLICTING` states, rebase, force-with-lease, merge, and `git branch -D` the squash-landed branches.
3. `issue-flow agent sync-branch` could not help at step 2: it replayed *all* ahead commits (including the ones already squash-landed on `master`) and aborted with conflicts in `.issueflows/04-designs-and-guides/incremental-load-protocol.md`, `.issueflows/04-designs-and-guides/test-registry.md`, and `HISTORY.md`, reporting "this needs a human decision".

The user's expectation: the drive confirm is an explicit, overnight authorization; under it the orchestrator should resolve routine conflicts, merge PRs, and keep going, not stop at the first non-trivial issue.

## Root causes (as read from the skills)

### A. Drive has no path for `yolo: no` issues

`/iflow-epic` records a per-issue yolo-fitness judgment, and the guide says umbrella work, design decisions and public-API changes are `no`. `/iflow-drive` then feeds **every** stage into `/iflow-auto` → `/iflow-cycle` → `/iflow-yolo`. Yolo's chain step 2 says "if the scope check reveals the change is not actually small, abort the yolo chain", and cycle 6c makes that a stop condition. So for any epic that contains a `yolo: no` issue (i.e. most real epics), drive is *guaranteed* to halt at the first such issue. The epic plan already knew this before the run started; drive did not look.

Proposals:

- **Preflight in drive**: read the `yolo:` flags of the stages it is about to run. If any is `no`, say so in the drive confirm and either refuse or ask which mode to use. Never let the run discover it one level down after two confirms.
- **A non-yolo lane for auto/cycle**: under the overnight/drive confirm, a `yolo: no` issue should run `capture → plan → build → close` with the *reasoning* profile and yolo's **scope check treated as advisory** (log it in the status file, don't abort). Merge policy for that lane should be configurable: `merge` (same as yolo), `pr-only` (open the PR, leave merge to the human, continue with the next issue stacked on the branch), or `stop`. Today only `stop` exists.
- Alternatively make `/iflow-cycle` accept `mode:full` (or `nonyolo`) so a queue of `yolo: no` issues can be processed hands-off under one confirm.

### B. Conflict handling is limited to one exact shape

`sync-branch` auto-resolves only additive `HISTORY.md` `[Unreleased]` bullets. In this run every conflict was equally mechanical bookkeeping:

- `.issueflows/04-designs-and-guides/test-registry.md` — both sides appended table rows.
- `.issueflows/04-designs-and-guides/*.md` design docs — both sides appended sections / edited the same trailing `## Link` block. (The squash-merge of #1102 even landed a duplicated `## Link` section on master, because GitHub's conflict editor was used with "keep both".)
- `HISTORY.md` — the shape sync-branch knows.

Proposals:

- Extend the additive resolver to every file under `.issueflows/04-designs-and-guides/` (registry tables, design-doc sections) and the issue status files, with the same rule: keep both, in-flight last. Keep the "anything else → stop" floor for product code.
- Make the drive/auto/cycle skills say explicitly that, under the overnight confirm, they **run sync-branch and retry the merge** for any conflict the resolver can handle, and only stop on a resolver exit 1.

### C. Stacked PRs / squash merges are not understood

Issues with `Depends on: #N` inside the same stage force branch stacking (the child needs the parent's code). After the parent squash-merges:

- the child branch still carries the parent's *unsquashed* commits, so GitHub retargets the PR to `master` and flags it `CONFLICTING`;
- `sync-branch` replays those already-landed commits and conflicts on every file they touched. It should detect squash-landed commits (`git cherry` / patch-id against `origin/<default>`, or `git range-diff`) and rebase `--onto origin/<default>` from the first commit that is *not* landed — the same logic `cleanup` already uses to classify `squash_landed`.
- there is no `sync-branch --onto <ref>` / `--base <parent-branch>` for a child PR whose base is another PR branch.

Also: `gh pr merge --squash` on #1103 reported "already merged" — an approval/auto-merge bot landed it while the skill was still watching checks. The skills should treat "already merged" as success, not as an error to report.

### D. Drive's constraints contradict what close does

`/iflow-drive` says "Never rebase / force-push / push default", while `/iflow-close yolo` (which drive composes) rebases via sync-branch and force-with-lease pushes. The drive constraint should be scoped to *the default branch* ("never rewrite or push default directly"), and explicitly allow the issue-branch rebase + `--force-with-lease` that close already owns.

### E. Drive cleanup is a no-op in squash repos

Drive's cleanup step is `git branch -d` on **reachable** branches only. With GitHub squash merges (the documented default) *every* merged branch is `squash_landed`, so `-d` never deletes anything. Under the drive confirm, `-D` for branches whose PR is `MERGED` and whose tip has zero `git cherry` unique commits is safe and should be allowed (the classification already exists in `agent cleanup`).

### F. Small things noticed

- The project's skills were baked at `0.4.2a4` while the CLI is 0.5.13; drive/auto/cycle have moved since. `issue-flow agent state` / `/iflow` could warn when the baked version is behind the installed CLI ("run `issue-flow update`").
- `graphify` rule in the project says to run `graphify query` when `graphify-out/graph.json` exists, but no graph existed; a cheap `if exists` check in the rule text avoids a wasted call per session.
- `dry-run` for drive should also print the yolo flags per queued issue, so a user can see up front that the run cannot complete unattended.

## Acceptance criteria

- `/iflow-drive <N>` on an epic containing `yolo: no` issues either (a) refuses at the confirm with the list of non-yolo issues, or (b) offers/uses a non-yolo lane (`capture → plan → build → close`) with a configurable merge policy, and completes the stage without stopping on the scope check.
- `issue-flow agent sync-branch` rebases past squash-landed commits and auto-resolves additive conflicts in `HISTORY.md`, `.issueflows/04-designs-and-guides/*.md` and issue status files; product-code conflicts still stop.
- `sync-branch` (or a new `stack-sync`) supports a child branch whose parent PR was squash-merged.
- Drive/auto/cycle skill text states that under the overnight confirm they resolve resolver-supported conflicts and retry the merge; "already merged" counts as success.
- Drive's constraint block no longer forbids the issue-branch rebase/force-with-lease that close performs.
- Drive cleanup may `-D` branches classified `squash_landed` with a `MERGED` PR under the drive confirm.
- Baked-skill-version vs installed-CLI drift is surfaced.

## Evidence

- cellpy: `.issueflows/01-current-issues/auto_status.md`, `drive_status.md` (stop reason + manual follow-up notes), PRs jepegit/cellpy#1101–#1104, epic plan `.issueflows/05-epics/epic783_plan.md` (all Stage 2/3 issues `yolo: no`).
- `sync-branch --json` output on `781-live-poll` after #1101/#1102 landed: `ahead: 4, behind: 2, conflicts: [incremental-load-protocol.md, test-registry.md, HISTORY.md]`, note "conflicts outside HISTORY.md … this needs a human decision".
