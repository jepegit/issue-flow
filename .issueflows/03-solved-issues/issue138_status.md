# Status — Issue #138: deterministic `issue-flow agent epic-status` CLI

- [x] Done

## Checklist

- [x] epicplan.py parser (header/status/stages/specs, `Depends on:` numbers +
      `stage <j> issue <k>` placeholders folded onto published targets,
      `## Later` ignored, lenient on prose)
- [x] gitutils.gh_issue_state (graceful None)
- [x] agent.run_epic_status (per-issue state, blockers, current stage,
      next unblocked candidates; --local skips gh; missing plan exits 1)
- [x] `agent epic-status` CLI command
- [x] Fast-path notes in the epic skill + command twin
- [x] Tests: 7 parser + 3 CLI (440 passed); docs/cli.md; HISTORY; scaffold
      regenerated
