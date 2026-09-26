# PR queue sync — refresh dirty open PRs after a merge

**Issue:** [#260](https://github.com/jepegit/issue-flow/issues/260)
**Status:** Part A implemented with the issue; Part B (`defer_changelog`) shipped in #288 (opt-in, default off).

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
   code conflicts still abort that head. Since #386 the same rule is applied
   per path to additive bullets / table rows in `04-designs-and-guides/*.md`
   and to `issue<N>_status.md` (`history.resolve_additive_conflict`;
   `sync-branch` payload `resolvers`). Product code is never auto-resolved.
2b. **Stacked children.** `sync-branch --base <ref>` replays only the commits
   after a squash-landed parent (`git rebase --onto`); auto-detected when an
   ancestor branch is provably landed — merged PR, zero `git cherry` unique
   commits, or `gitutils.content_landed` (touched files byte-identical on
   `origin/<default>`). Payload: `base`, `base_detected`, `dropped_commits`.
3. **Default candidates = dirty only.** `--all-open` is opt-in.
4. **Ephemeral worktrees.** `../<repo>-prsync-<branch>` created as needed and
   removed by default (`--keep-worktrees` to retain).
5. **Prevention shipped (#288).** Optional `defer_changelog` writes the bullet
   on the default branch after merge (`issue-flow agent apply-changelog`).
   Default **off** — this skill stays the repair path when issue branches
   still edit HISTORY.

## Links

[changelog-conflicts.md](./changelog-conflicts.md),
[changelog-timing.md](./changelog-timing.md),
[parallel-cycle.md](./parallel-cycle.md).
