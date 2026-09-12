# Issue #255: Worktree + separate window on pick/issue start (keep home on default)

Source: https://github.com/jepegit/issue-flow/issues/255

## Original issue text

## Problem / context

#253 shipped `issue-flow agent open-workspace` and wired it only into `/iflow-cycle` `parallel:<n>`. Normal start (`/iflow-pick`, `/iflow-issue`, `/iflow-fix`) still does `git switch -c` on the **home checkout**. Opening a terminal in the project folder then shows the agent's issue branch (reproduced in cellpy). The helper never creates a worktree; callers must `git worktree add` first. Home should stay on the default branch when an agent starts work.

## Spec

- On confirmed start from `/iflow-pick`, `/iflow-issue` Phase 2, and `/iflow-fix` branch create: `git worktree add ../<repo>-<N> <N>-<slug>` (or equivalent next to the home root), then `issue-flow agent open-workspace <worktree> --json`. Pass `--open` only after confirm (same rule as #253).
- Leave the **home** working tree on the default branch (fast-forward if needed). Do not `git switch` the home checkout onto the issue branch.
- Document the pattern in `separate-workspaces.md` and pick/issue/fix skills + commands. Extend `open-workspace` only if needed to create/list the worktree path (prefer skill + existing `git worktree add` unless a small CLI helper is clearly better).
- `/iflow-cleanup` (and close/switchback as needed) must know about the worktree: remove it after merge when safe; never delete unique work. Home stays the coordinator checkout.
- Ops exception unchanged: ops may stay on current/default without a worktree when the user chooses that.

## Acceptance criteria

- [ ] Pick / issue Phase 2 / fix branch-create skills instruct worktree-first, home stays on default.
- [ ] `open-workspace` print → confirm → `--open` used; no silent window spawn.
- [ ] Design/guide updated (separate-workspaces vs in-place `git switch`).
- [ ] Cleanup/close guidance removes or reports the worktree after a landed PR; home checkout never left on the issue branch by start-work.
- [ ] Tests or a short checklist cover “home still on default after start” and “no auto `--open`”.

## Out of scope

- Changing `agent resolve` / multi-root registry.
- Forcing worktrees in headless/CI.
- Cross-repo parallel cycles.
- Making sequential `/iflow-cycle` (non-`parallel:<n>`) use worktrees (optional follow-up).
