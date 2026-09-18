# Changelog timing — in the PR, or deferred until default

**Issue:** [#171 — Timing of updating changelog](https://github.com/jepegit/issue-flow/issues/171)
**Status:** decided 2026-07-19, implemented in the same issue.
**Follow-up:** [#288 — `defer_changelog`](https://github.com/jepegit/issue-flow/issues/288)
writes on the default branch after merge when the knob is on (default **off**).

## Context

Agents sometimes asked about `HISTORY.md` / CHANGELOG **after** a PR was
accepted or merged. `/iflow-close` already updates the changelog in step 3
(before commit / push / PR), but confirm-decline used to skip and continue,
so PRs could land without a bullet — inviting a post-merge ask.

Two issue branches appending `[Unreleased]` still collide (#240 / #260).
`defer_changelog` is the **prevention** path: the issue branch never touches
the file. Repair (`sync-branch` / `pr-sync`) stays the default-off path.

## Decisions

1. **Reuse `confirm_changelog_update`** — it still gates *whether / what text*.
   It does not choose *when* the file is written.
2. **Default `false`** — write without asking so the bullet lands in the PR
   commit (same as yolo history behaviour). Projects can set `true` for a
   confirm gate.
3. **Decline is blocking** (when confirm is on) — stop close; offer write /
   revise / `nohistory` / abort. No silent skip-and-continue.
4. **Never invent a post-close *offer*** — close, history-update, cleanup, and
   rules forbid proposing a *new* HISTORY/CHANGELOG bullet after close has
   finished or after merge. A draft opened earlier via `/iflow-build` early PR
   does **not** skip close's HISTORY *decision*.
5. **`defer_changelog` (default off, #288)** — when on, step 3 still decides
   the bullet (`nohistory` / `log` / confirm) but writes
   `### Deferred changelog` on `issue<N>_status.md` and the PR body instead of
   `HISTORY.md`. `/iflow-cleanup` A1 and yolo post-pull run
   `issue-flow agent apply-changelog --issue N` on the **default** branch
   (from **home** even under `stay`) and commit `docs: changelog for #<N>`
   when it wrote. That apply is not a new offer.

## Link

Issue #171 / #288; knob table in [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).
Conflict *repair*: [changelog-conflicts.md](./changelog-conflicts.md) (#240),
[pr-queue-sync.md](./pr-queue-sync.md) (#260 Part A).
