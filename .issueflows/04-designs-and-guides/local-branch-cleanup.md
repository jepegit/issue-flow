# Local branch cleanup under squash merges

**Issue:** [#243 — `/iflow-cleanup` cannot prune squash-merged branches](https://github.com/jepegit/issue-flow/issues/243)
**Status:** decided 2026-09-04, implemented in the same issue.
**See also:** [`github-branch-audit.md`](github-branch-audit.md) (the *remote*
half, issue #163), whose bucket/confirm conventions this mirrors.

## Context

`/iflow-cleanup` promised to delete "every local branch whose tip is already
reachable from `origin/<default>` (include squash-merges via `git cherry`)"
using `git branch -d`, while forbidding `-D`.

Those rules cannot both hold. `git cherry` proves **patch equivalence**;
`git branch -d` requires **reachability** (from HEAD or from the branch's own
upstream). A squash merge lands a *new* commit on the default branch, so the
branch tip is never an ancestor of it. Once the PR merge deletes the remote
branch and `git fetch --prune` drops the remote-tracking ref, `-d` refuses
forever — and cleanup reported success while pruning nothing.

Observed 2026-09-04 after #242 merged: all 15 local branches were
squash-merged, `git branch --merged main` was empty, and 14 were provably
landed. They had to be removed by hand with `-D`, the one operation the skill
forbade. Branches had been accumulating since #125.

## Decisions

### 1. Five buckets, not three

| Bucket | Rule | Deletion |
| --- | --- | --- |
| `reachable` | Ancestor of `origin/<default>` | `-d`, inside the Phase A1 confirm |
| `squash_landed` | Not reachable, but `git cherry` reports no unique commits | `-D`, only after the Phase A2 confirm |
| `merged_pr_divergent` | Not reachable, has unique commits, has a merged PR, and **no** unique commit newer than `mergedAt` | `-D`, only after the Phase A2 confirm, listed separately |
| `unique_work` | Unique commits with no merged PR, an open PR, or a commit newer than the merge | never |
| `skipped` | Current branch, default branch, protected, uncomparable | never |

`merged_pr_divergent` earns its own bucket because the real repo produced it:
`137-epic-publish` (PR #147), `138-epic-status-cli` (#148) and
`237-doctor-editor-scaffold` (#238) each had a merged PR *and* commits that
`git cherry` still called unique, because the squash rewrote them. Folding
those into `squash_landed` would delete on weaker proof; folding them into
`unique_work` would strand them forever.

### 2. The date check that keeps A2 safe

A merged PR plus unique commits has two very different causes, with identical
bucket counts:

- the squash **rewrote** the branch's commits — nothing is at risk;
- work was **pushed after** the PR merged — genuinely unmerged.

They are told apart by comparing the newest unique commit's committer date
(`git log --no-merges --format=%cI`) against the PR's `mergedAt`. Anything
newer than the merge means `unique_work`.

This is not hypothetical: `review-improvements` (PR #127) has one unique
commit, and only the timestamps distinguish it. Comparing the ISO strings
lexically gets it **wrong** — `2026-07-09T23:41:19+02:00` looks later than
`2026-07-09T22:18:50Z` but is 37 minutes earlier — so both sides are parsed to
aware datetimes, and an unparseable timestamp falls back to the cautious
answer (`unique_work`).

### 3. Narrow relaxation of the "never `-D`" rule

`-D` is now permitted, but only: for `squash_landed` / `merged_pr_divergent`
branches, after a **Phase A2 confirm separate from Phase A1**, with each
branch's tip SHA printed (recover with `git branch <name> <tip>`). Never for
`unique_work`, never for an unclassifiable branch, never for the current
branch, and never from the `/iflow-yolo`, `/iflow-cycle`, or `/iflow-auto`
chains, which cannot show a human the list.

A `-d` refusal in Phase A1 is still reported and left alone — it is not a
licence to escalate. Within Phase A2, `-d` is tried first anyway, because it
also accepts branches merged into their own upstream and sometimes still
succeeds; `-D` is the fallback.

### 4. `agent local-branches` as its own command

A separate read-only subcommand rather than a `--local` flag on
`agent branches`: the payload shapes differ (`reachable` / `squash_landed`
vs `deletable`), and rendered skills already in the wild consume today's
`agent branches` payload. Deletes stay in the skill, per #163 §4.

PR evidence comes from **one** batched `gh pr list … --json …,headRefName`
indexed by head, not one call per branch as the remote audit does — 15 local
branches otherwise cost 15 round trips. Protection is checked only for
branches that are already deletion candidates.

## Alternatives considered

- **Report-only, user deletes by hand** — rejected; that is the status quo that
  let branches pile up for 100+ issues.
- **Escalate to `-D` whenever `-d` refuses** — rejected; `-d` refuses for
  unmerged work too, which is exactly what must be protected.
- **Trust a merged PR alone** — rejected; it cannot see commits pushed after
  the merge (see decision 2).

## Link

Issue #243, `issue243_plan.md`.
