# Status: #303 Default-branch diverge

- [x] Done

## What's done

- `issue-flow agent default-sync --json` classifies unique default-branch commits (no mutate).
- `worktree-add` fetches and still starts from `origin/<default>` when home is ahead.
- switchback attaches `default_sync` on ff-only refusal and when home is ahead.
- Skills/commands: pick/issue/fix start no longer require home FF; cleanup/close recover via the action table; epic/doctor/init must not leave unpushed commits on default.
- Design note: `.issueflows/04-designs-and-guides/default-branch-diverge.md`.
- Version `0.5.4`. Tests + ruff green.

## Remaining work

- None.
