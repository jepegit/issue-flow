# Status — Issue #140: deterministic `issue-flow agent queue` CLI

- [x] Done

## Checklist

- [x] queueplan.py — `parse_dependencies` (marker lines only), `build_queue`
      (Kahn toposort, numeric tie-break, blocked/skipped_closed/independent,
      cycle detection)
- [x] gitutils.gh_issue_meta / gh_issue_list_meta
- [x] agent.run_queue + `agent queue` CLI (numbers / --label / --epic,
      mutually exclusive; partial-fetch refusal; epic uses current stage)
- [x] Tests: 7 queueplan + 6 CLI (453 passed)
- [x] docs/cli.md row + synopsis; HISTORY entry

## Notes

`independent` (no dependency relation to any other member) is the
parallel-safe signal that stage 3 (#143) consumes. `/iflow-cycle` (#141)
consumes the ordered queue.
