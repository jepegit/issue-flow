# Parallel cycle dispatch (experimental)

Context: issue #143 — the cycling-mode epic (#145) stage 3. When the editor
harness supports background execution, **provably independent** issues in a
cycle could run in parallel. This is deliberately the last slice and stays
**opt-in and experimental**: parallelism multiplies failure modes, and the
sequential cycle must always work everywhere without it.

## Hard constraints

- **Only independent issues qualify.** Use `issue-flow agent queue --json`:
  an issue is eligible only when it appears in the `independent` list — i.e.
  it has **no dependency relation, in either direction, to any other queue
  member**. Anything with an edge (even to a blocked relative) runs
  sequentially.
- **Sequential remains the default and is never weakened.** Parallelism is
  requested explicitly (`parallel:<n>`); with no such token the cycle runs
  exactly as before. No safeguard is relaxed to enable parallelism.
- **Merges are serialized.** PRs never merge concurrently. The coordinating
  session merges them one at a time on the default branch, rebasing / re-running
  tests on a refusal. Concurrent merges race on the default branch and on CI.
- **Shared files are written only by the coordinator, in merge order.** The
  worst offender is `HISTORY.md`: parallel workers must **not** each
  edit it. Each worker leaves its changelog bullet in its own issue status
  file (or PR body); the coordinator appends the bullets to `HISTORY.md`
  during the serial merge step, in the order merges land.

## Execution pattern (per-issue worktree)

1. Resolve the independent subset from `agent queue`.
2. For each, `git worktree add ../<repo>-<N> <N>-<slug>` so every issue gets
   an isolated working tree on its own branch — no shared index, no collisions.
3. Run the yolo chain (minus its own merge/close-to-default steps) in each
   worktree, in the background where the harness allows.
4. **Serial merge queue:** the coordinator opens/merges each PR one at a time
   (`--squash`), pulling the default branch between merges; on a non-fast-forward
   or CI refusal it rebases that branch and retries, or falls back to sequential
   for the remainder.
5. Append the deferred `HISTORY.md` bullets in merge order, then
   `git worktree remove` each worktree.

## Per-harness notes (capabilities move fast — verify before relying)

- **Cursor** — background agents / parallel chats can drive worktrees; there is
  no first-class "wait for all" primitive, so the coordinator polls PR state.
- **Claude Code** — subagents and `git worktree` support make the
  worktree-per-issue pattern natural; the parent session is the coordinator.
- **opencode / Codex** — background execution varies; when unavailable, refuse
  `parallel:<n>` and run sequentially.

Detection is best-effort: if the skill cannot confirm the harness supports
background execution, it **refuses `parallel:<n>` and runs sequentially** —
never silently pretending to parallelize.

## Out of scope

- **Cross-repo parallel cycles** — combining this with the workspace registry
  (multiple member repos in one run) is a possible follow-up, not covered here.
- Any weakening of the sequential path.
