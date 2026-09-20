# Status: #317 Help agents watch until a PR is merge-ready

- [x] Done

## What's done

- `issue-flow agent pr-ready [N] [--watch]` — classify + poll, never merges.
- `classify_pr_ready` / `run_pr_ready`; `gh_pr_view` takes optional number +
  rollup fields.
- Tests: ready / UNSTABLE optional / blocked / missing / watch timeout.
- gh-ci + close offer `pr-ready --watch`; docs + design note updated.
- HISTORY bullet under Unreleased.

## Remaining work

- None.
