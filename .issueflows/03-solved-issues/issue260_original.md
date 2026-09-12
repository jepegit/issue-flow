# Issue #260: Multi-PR HISTORY conflicts: pr-sync refresh + optional defer_changelog

Source: https://github.com/jepegit/issue-flow/issues/260

## Original issue text

## Problem / context

When several PRs are open and one merges (especially with a `HISTORY.md` / version bump), sibling PRs become `DIRTY` / “needs update”. GitHub’s Update branch cannot resolve additive `[Unreleased]` bullets or promoted version headings. `#240` / `issue-flow agent sync-branch` only fixes the *current* close branch — not the rest of the queue.

Real case: PR #259 went `CONFLICTING` after `#255` landed `0.4.13`; auto sync aborted on non-HISTORY files + dual `0.4.13` promotions.

## Spec

### 1. Repair — `/iflow-pr-sync` (primary)

- Off-path skill + command: refresh open PR heads that are behind / `DIRTY`.
- CLI: `issue-flow agent pr-sync` (or similar) looping: fetch → checkout/worktree head → reuse `sync-branch` / `history.py` keep-both → `git push --force-with-lease` (CLI may need an explicit push flag; never bare `--force`).
- One consolidated confirm listing PRs/branches; skip/stop on non-auto-resolvable conflicts; never `--admin`.
- Wire: offer after `/iflow-cleanup` when siblings remain; after yolo merge when more open PRs exist.
- Design doc: extend `changelog-conflicts.md` or add `pr-queue-sync.md`.

### 2. Prevent — `defer_changelog` knob (same issue if small enough; else follow-up)

- Optional `[issueflow].defer_changelog` (default `false`): close writes the bullet into status/PR body only; append (and version promote) on default **after** merge (`/iflow-cleanup` or yolo post-pull).
- Document bump interaction (no dual `0.4.x` promotions on parallel issue branches).

## Acceptance criteria

- [ ] `issue-flow agent pr-sync` (or named equivalent) can refresh a DIRTY open PR whose only conflict is keep-both `[Unreleased]` HISTORY, then force-with-lease push.
- [ ] `/iflow-pr-sync` skill documents the confirm, skip rules, and cleanup/yolo hooks.
- [ ] Tests cover the multi-head loop (mocked git/gh) and refuse non-HISTORY conflicts.
- [ ] Design doc records prevent vs repair decision; if `defer_changelog` ships here, knob is baked + documented; otherwise a linked follow-up issue exists.
- [ ] Docs / rules mention the new skill next to changelog-conflicts guidance.

## Out of scope

- Changing squash-merge policy.
- Auto-merging the refreshed PR queue without an explicit confirm.
- Resolving arbitrary code conflicts (still human / stop).
