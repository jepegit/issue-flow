---
title: Refresh dirty open PRs
---

# Refresh dirty open PRs

## Goal

When another merge (often `HISTORY.md`) leaves sibling open PRs `DIRTY`, refresh
those heads without losing keep-both changelog bullets.

## Steps

1. On a clean default-branch checkout (or wherever you normally run ops), run
   `iflow pr-sync` (or `/iflow-pr-sync`).
2. Review the candidate list (default: dirty open PRs only).
3. Confirm once. For each head the agent uses a worktree, runs
   `issue-flow agent sync-branch` (keep-both for `[Unreleased]` HISTORY
   collisions, for additive bullets / table rows in
   `04-designs-and-guides/*.md`, and for `issue<N>_status.md`), then
   `git push --force-with-lease`.
4. Re-check the PRs on GitHub; merge when green.

A head that was branched from **another** issue branch which has since been
squash-merged would normally conflict on every file the squash rewrote.
`sync-branch` detects that parent when it is provably landed and replays only
the child's own commits (`base_detected` in the JSON). If detection does not
fire, run it yourself in that head's worktree:

```bash
issue-flow agent sync-branch --base <parent-branch-or-sha> --json
```

Anything outside those bookkeeping files — product code, a renamed heading,
an edited line — still stops the batch for a human decision.

CLI mirror for agents: `issue-flow agent pr-sync` (non-interactive — the skill
owns the confirm).

## Related

- [Command reference](../issue-workflow.md) — `/iflow-pr-sync` reference
- [CLI](../cli.md) — `agent sync-branch` / `agent pr-sync`
- [After a squash merge](after-squash-merge.md)
