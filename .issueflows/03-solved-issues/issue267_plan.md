# Plan — Issue #267: chore: remote branch audit (2026-09-12)

## Goal

Re-check the 2026-09-12 remote-branch findings and only delete a remote
when its tip work is already on `main`.

## Scope check — abort yolo

Not a small hands-off change. `issue-flow agent branches` on 2026-09-26
still puts three remotes in `unique_work`, and the issue says not to
delete those without a review:

- `140-agent-queue-cli` — 3 commits, no merged PR (`111c6fb`)
- `cursor/163-github-branches-e2ca` — merged PR #188, tip still differs (`6302079`)
- `cursor/gha-sync-issueflows-08d1` — merged PR #160, tip still differs (`d765ca5`)

Deleting them is a destructive remote op. Deciding that the tips are
discarded or already recovered is a human call. Yolo stops here. No
build, no push, no remote delete.

## Approach

None in this cycle. Inspect the three tips, then delete by hand only
the ones whose work is already on `main`.

## Files to touch

None.

## Test strategy

None. No product change.
