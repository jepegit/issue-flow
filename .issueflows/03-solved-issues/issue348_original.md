# Issue #348: docs: slim the home page and unify the quick start

Source: https://github.com/jepegit/issue-flow/issues/348

## Original issue text

## Context and spec

Rewrite `docs/index.md` as: a concrete benefit statement (replacing the current "Why" section), a small lifecycle overview, three entry points (New to issue-flow → Getting started; Want to do X → How-to; AI agent → For agents / llms.txt), and an install one-liner. Move the recipes into the How-to index. Use one canonical quick start (`iflow pick → plan → build → close → cleanup`) on Home, Getting started and README. Make the file tree editor-neutral, or put it in tabs per editor (`pymdownx.tabbed`). See review §3, §12.

**Goal:** the home page fits roughly one screen plus the entry points, and Home, Getting started and README show the same quick start.

**Model:** deep

Depends on: #347

Full review: `.issueflows/04-designs-and-guides/docs-usability-review.md`.

Part of epic #341.
