# Issue #56 — rename from build to graphify

- **URL:** https://github.com/jepegit/issue-flow/issues/56
- **State:** OPEN

## Description

The current markdown file is called build.md for building the graphify graph. This should be renamed to build-graphify (and the correspoinding slash command would then be /graphify).

## Resolved scope (confirmed with user 2026-06-06)

The issue body is internally inconsistent ("renamed to build-graphify" vs. slash command "/graphify"). Confirmed decisions:

- New slash command is **`/graphify`** (file `graphify.md`, skill `issueflow-graphify`).
- The CLI subcommand **`issue-flow build` is also renamed to `issue-flow graphify`** for consistency.
