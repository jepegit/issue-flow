# Changelog timing — always in the PR

**Issue:** [#171 — Timing of updating changelog](https://github.com/jepegit/issue-flow/issues/171)
**Status:** decided 2026-07-19, implemented in the same issue.

## Context

Agents sometimes asked about `HISTORY.md` / CHANGELOG **after** a PR was
accepted or merged. `/iflow-close` already updates the changelog in step 3
(before commit / push / PR), but confirm-decline used to skip and continue,
so PRs could land without a bullet — inviting a post-merge ask.

## Decisions

1. **Reuse `confirm_changelog_update`** — no new config key.
2. **Default `false`** — write without asking so the bullet lands in the PR
   commit (same as yolo history behaviour). Projects can set `true` for a
   confirm gate.
3. **Decline is blocking** (when confirm is on) — stop close; offer write /
   revise / `nohistory` / abort. No silent skip-and-continue.
4. **Never post-merge** — close, history-update, cleanup, and rules forbid
   offering a HISTORY/CHANGELOG update after the PR is open or merged.

## Link

Issue #171; knob table in [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
