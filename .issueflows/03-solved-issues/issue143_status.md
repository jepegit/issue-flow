# Status — Issue #143: parallel dispatch for independent issues (experimental)

- [x] Done

## Checklist

- [x] Design record `.issueflows/04-designs-and-guides/parallel-cycle.md`
      (constraints + per-harness notes) — this repo's own design record,
      following the release-strategies.md / multi-repo-workspaces.md pattern
- [x] Cycle skill: opt-in `parallel:<n>` section (independent-only, harness
      gate, worktree-per-issue, serial merge queue, HISTORY via coordinator);
      "sequential is the default and floor" constraint
- [x] Cycle command twin: `parallel:<n>` input mention
- [x] Tests: cycle-skill parallel contract (460 passed)
- [x] HISTORY; scaffold regenerated

## Notes

Chose a plain design record over a scaffolded design template: the doc names
Cursor/Claude/Codex per-harness (tripping the non-cursor leakage guard when
scaffolded), and issue-flow's own design records (release-strategies.md,
multi-repo-workspaces.md) live in this repo's design folder, not as
templates. The cycle skill's inline parallel section carries the operational
rules for scaffolded projects.
