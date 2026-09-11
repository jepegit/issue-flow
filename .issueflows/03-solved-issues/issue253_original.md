# Issue #253: Run parallel / multi-repo agent work in separate Cursor workspaces

Source: https://github.com/jepegit/issue-flow/issues/253

## Original issue text

## Problem / context

Multi-root Cursor workspaces (#67, #126) and parallel-cycle worktrees (#143) still leave agents sharing one editor workspace. Shared context mixes rules, cwd, and `agent resolve` signals. Crosstalk hurts when several issues or sibling repos run at once.

## Spec

- Prefer **one Cursor workspace (window) per active worktree / member repo** for parallel or concurrent agent runs; coordinator stays in the parent/home workspace.
- Document the pattern next to multi-root + parallel-cycle guides (when to use separate windows vs multi-root).
- Add a small helper (CLI or skill step) that, for a worktree or registry member, prints/opens the path to launch as its own workspace (e.g. `cursor <path>` / equivalent) — no silent auto-spawn without confirm.
- Parallel cycle (`parallel:<n>`): each independent worker’s worktree is opened or addressed as a **separate** workspace when the harness allows; serial merge + HISTORY still owned by the coordinator (unchanged from #143).
- Keep existing multi-root + `issueflow-workspace.toml` resolution; this is an **execution layout**, not a replacement for the registry.

## Acceptance criteria

- [ ] Design/guide covers separate-workspace vs multi-root trade-offs and the coordinator/worker split.
- [ ] Helper or skill steps exist to launch/address a worktree or member as its own workspace behind confirm.
- [ ] Parallel-cycle skill (when `parallel:<n>`) documents/uses separate workspaces per worker where harness supports it; refuses gracefully otherwise (same as today’s background-exec gate).
- [ ] Serial merge, HISTORY via coordinator, and sequential default remain unchanged.
- [ ] Tests or a short manual checklist cover the helper + “no auto-open without confirm”.

## Out of scope

- Cross-repo parallel cycles (already out of #143).
- Replacing multi-root registry / `agent resolve`.
- Force-opening editor windows in headless/CI.
