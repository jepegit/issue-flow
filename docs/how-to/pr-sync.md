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
   collisions), then `git push --force-with-lease`.
4. Re-check the PRs on GitHub; merge when green.

CLI mirror for agents: `issue-flow agent pr-sync` (non-interactive — the skill
owns the confirm).

## Related

- [The workflow](../issue-workflow.md) — `/iflow-pr-sync` when documented in your scaffold
- [CLI](../cli.md) — `agent sync-branch` / `agent pr-sync`
- [After a squash merge](after-squash-merge.md)
