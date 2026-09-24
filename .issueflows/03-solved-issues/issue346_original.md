# Issue #346: docs: regroup navigation and the How-to index

Source: https://github.com/jepegit/issue-flow/issues/346

## Original issue text

## Context and spec

In `zensical.toml`, regroup the nav into Getting started (with Choose a mode and Editor support moved in), Concepts (placeholder until the next issue), How-to guides (sub-groups Everyday / Faster / Bigger changes / Team and repos), Reference (Commands, CLI, Configuration, Graphify), For agents, and Project (Developing, Changelog, Acknowledgements). Do not rename files. Rewrite `docs/how-to/index.md` as grouped tables that match the new nav. Evaluate `navigation.tabs` and enable it if it makes the sidebar shorter. See review §4.

**Goal:** the nav matches the grouping above, no file under `docs/` is renamed, and the link check passes.

**Model:** default

Depends on: #344

Full review: `.issueflows/04-designs-and-guides/docs-usability-review.md`.

Part of epic #341.
