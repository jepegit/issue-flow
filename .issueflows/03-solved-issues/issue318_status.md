# Status: #318 workspace-wide actions

- [x] Done

## What's done

- Plan accepted.
- `iter_workspace_members` extracted; `workspace update` uses it.
- CLI: `workspace status [--local] [--json]`, `workspace doctor [--json]`
  (audit only), `workspace dirty [--json]`. Locked members skipped;
  continue-on-fail.
- Skills/commands: `/iflow-status` + `/iflow-doctor` workspace token;
  `/iflow-cleanup workspace` sequential per-member loop.
- Docs: `docs/cli.md`, `docs/how-to/workspaces.md`,
  `multi-repo-workspaces.md` Phase 4.
- Tests: `tests/test_workspace_actions.py` + `iter_workspace_members` units
  (marked essential). Registered `essential` pytest marker.
- HISTORY bullet under Unreleased.

## Remaining work

- None.
