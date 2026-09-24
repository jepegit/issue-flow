# Plan — Issue #343: docs: replace links into .issueflows/ and apply small wording fixes

(yolo chain via /iflow-drive 341 → /iflow-auto → /iflow-cycle; auto-confirmed.)

## Goal

The built site has no relative links to `.issueflows/`, and the review §13 wording fixes are in.

## Approach

- `configuration.md`: change the three `../.issueflows/04-designs-and-guides/*.md` links to GitHub blob URLs.
- `editors.md`, `how-to/worktrees.md` and `how-to/auto-mode.md` said the design docs exist "in scaffolded projects" / "after `issue-flow init`". Verified false: init only seeds `this-project.md`, `essential-tests.md` and `test-registry.md`. Link to the GitHub copies instead.
- `cli.md`: fix the unclear sentence about the folded synopsis, and mark the `agent …` helpers as mostly for skills.
- `getting-started.md`: add a "Before you start" list (editor + agent, GitHub account, expected time).

## Test strategy

`uvx zensical build`, then grep `site/` for relative `.issueflows` hrefs. `uv run pytest`.
