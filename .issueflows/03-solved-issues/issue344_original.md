# Issue #344: ci: add a link check on the built docs site

Source: https://github.com/jepegit/issue-flow/issues/344

## Original issue text

## Context and spec

Add a CI job (in `ci.yml` or a new docs workflow) that runs `uv run zensical build` and then a link checker (e.g. `lychee` via its GitHub Action) on `site/`. Internal links must be checked and must fail the job. External links should be checked with retries, or reported only as warnings, so flaky third-party sites don't block PRs. Document how to run the check locally in `docs/developing.md`. See review §2 "Guard".

**Goal:** a PR that introduces a broken internal doc link fails CI; the current `main` passes.

**Model:** default

Depends on: #342, #343

Full review: `.issueflows/04-designs-and-guides/docs-usability-review.md`.

Part of epic #341.
