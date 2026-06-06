# Issue #55 plan: agent tab improvement

## Goal
Add an instruction to `/issue-init` so the agent renames the chat/agent tab to reflect the issue topic.

## Approach
Append one bullet to step 2 of `.cursor/commands/issue-init.md`, after the "Confirm resolved `owner/repo`" bullet:

> - Change the chat/agent tab title to reflect the issue topic on the form "Issue <issue number> <short description of issue>", for example "Issue 74 cell info".

## Files to touch
- `.cursor/commands/issue-init.md`

## Test strategy
Docs-only change to a command file; no code paths affected. Run `uv run pytest` to confirm the suite still passes (no regressions expected).
