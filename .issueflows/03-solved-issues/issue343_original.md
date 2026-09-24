# Issue #343: docs: replace links into .issueflows/ and apply small wording fixes

Source: https://github.com/jepegit/issue-flow/issues/343

## Original issue text

## Context and spec

`docs/configuration.md` links to `../.issueflows/04-designs-and-guides/*.md`, which is outside the published site (404). Replace each with the GitHub blob URL, or summarise the decision inline. Where plain-text mentions of `.issueflows/04-designs-and-guides/…` refer to the reader's scaffolded project, say so explicitly. Also apply the wording fixes from review §13: the unclear "folded at the bottom of this page intro" sentence in `cli.md`; mark the `agent …` helpers as "called by skills"; state prerequisites and expected time at the top of `getting-started.md`. Commit `docs-usability-review.md` in this PR if the previous issue did not. See review §2, §13.

**Goal:** the built `site/` contains no relative links to `.issueflows/`, and the three wording fixes are in.

**Model:** fast

Depends on: none

Full review: `.issueflows/04-designs-and-guides/docs-usability-review.md`.

Part of epic #341.
