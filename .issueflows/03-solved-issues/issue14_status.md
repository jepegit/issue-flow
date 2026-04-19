# Issue #14 status: Add a history file

Source: https://github.com/jepegit/issue-flow/issues/14

## Summary

The repo had no release history file. Added a top-level `HISTORY.md` that
documents every published release (v0.1.0 through v0.2.2) plus an
`## [Unreleased]` section for changes landed on `main` since v0.2.2
(PRs #35, #36, #37, #38). Linked it from `README.md` under a new
"Changelog" section.

## What was done

- Created `HISTORY.md` at the repo root.
  - Loose "Keep a Changelog" format.
  - Sections for every released tag: `0.2.2`, `0.2.1.post2`, `0.2.1.post1`,
    `0.2.1`, `0.2.0`, `0.1.4`, `0.1.3`, `0.1.2`, `0.1.1`, `0.1.0`.
  - `## [Unreleased]` section populated with work merged after v0.2.2
    (`.env` scaffolding, `ISSUEFLOW_AGENT_DIR` rename, `/issue-close`
    improvements, branch & folder hygiene).
  - Noted that pre-0.2.2 entries are reconstructed from git log /
    PR titles and link back to the GitHub release page.
- Added a short "Changelog" section in `README.md` pointing to
  `HISTORY.md`.

## Files changed

- `HISTORY.md` (new)
- `README.md` (added "Changelog" section linking to `HISTORY.md`)

## Remaining work

- None — the issue only asks for a HISTORY file to exist. Future version
  bumps via `/issue-close` should move entries from `## [Unreleased]`
  into a new versioned section.

## Status

- [x] Done
