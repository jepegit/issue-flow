# Status — Issue #133: deterministic version-plan fast path

- [x] Done

## Current status

Implemented on branch `133-version-plan-cli` (stacked on
`125-version-bump-strategy` / PR #134).

## Checklist

- [x] `versionplan.py`: PEP 440 subset parser/formatter, sequential bump ops
      (canonical order, forward-only pre-release channels, `v` prefix kept),
      pre-release-aware defaults, strategy detection (static / setuptools-scm
      / hatch-vcs / versioningit / unknown)
- [x] `gitutils.latest_tag()` (describe, falling back to version-sorted list)
- [x] `agent.run_version_plan` + `issue-flow agent version-plan` CLI
      (read-only; reports `brief_release_section` so the brief still wins)
- [x] `iflow-version-bump` skill: CLI fast path note
- [x] Tests: versionplan unit suite + 5 CLI tests; full suite 426 passed
- [x] Docs (`docs/cli.md`), HISTORY, scaffold regenerated
- [x] Live-verified: static (issue-flow itself, brief correctly flagged) and
      a tag sandbox reproducing the #125 cellpy case
      (`v1.0.4a2` + default → planned `v1.0.4a3`, tag deferred to post-merge)

## Remaining work

None.
