# PR queue sync — refresh dirty open PRs after a merge

**Issue:** [#260](https://github.com/jepegit/issue-flow/issues/260)
**Status:** Part A implemented with the issue; Part B (`defer_changelog`) optional follow-up.

## Context

`#240` / `issue-flow agent sync-branch` fixes the *current* close branch when
`HISTORY.md` collides under `[Unreleased]`. It does **not** help sibling open
PRs that go `DIRTY` after another squash lands (or after a version promote).
GitHub’s “Update branch” cannot keep-both bullets and fails hard on promoted
version headings (as with dual `0.4.13` promotions on #255 vs #259).

## Decisions

1. **Repair skill + CLI first.** `/iflow-pr-sync` and
   `issue-flow agent pr-sync` loop: worktree → `sync-branch` →
   `git push --force-with-lease`. Explicit confirm in the skill; CLI itself is
   non-interactive (agent owns the confirm).
2. **Reuse keep-both.** No second resolver — same `history.py` rules; heading /
   code conflicts still abort that head.
3. **Default candidates = dirty only.** `--all-open` is opt-in.
4. **Ephemeral worktrees.** `../<repo>-prsync-<branch>` created as needed and
   removed by default (`--keep-worktrees` to retain).
5. **Prevention later.** Optional `defer_changelog` (write bullet on default
   after merge) remains the structural fix for bump collisions; tracked as
   Part B of #260 / follow-up.

## Links

[changelog-conflicts.md](./changelog-conflicts.md),
[changelog-timing.md](./changelog-timing.md),
[parallel-cycle.md](./parallel-cycle.md).
