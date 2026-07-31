# GitHub remote branch audit in `/iflow-cleanup`

**Issue:** [#163 — How to handle branches on GitHub](https://github.com/jepegit/issue-flow/issues/163)
**Status:** decided 2026-07-20, implemented in the same issue.

## Context

Local `/iflow-cleanup` already deletes merged *local* branches. Remotes on
GitHub often accumulate after squash merges, abandoned experiments, and
stale agent branches. Users need a way to ask issue-flow what is safe to
delete, what still has unique commits, and optionally file the findings.

## Decisions

### 1. Opt-in via trailing tokens (or config) on `/iflow-cleanup`

Recognise (case-insensitive): `include github`, `include gh`, `with github`,
standalone `github`. Default cleanup stays Phase A only (local), unless
`[issueflow].cleanup_include_github = true` is baked at `issue-flow update`
(issue #233). Opt out of a baked-on Phase B with `no github` / `local only` /
`local-only`.

**Enable rule:** (`cleanup_include_github` **or** opt-in token) **and** no
opt-out token.

### 2. Two confirms

- **Phase A** — existing local consolidated confirm (`git branch -d`, never `-D`).
- **Phase B** — separate confirm for remote deletes (`git push origin --delete`,
  never `--force`) and optional findings issue. Phase A yes never implies
  Phase B actions.

### 3. Classification buckets

| Bucket | Rule |
| --- | --- |
| `deletable` | Tip fully in `origin/<default>` (`git cherry` has no `+` lines) and no open PR |
| `unique_work` | Has unique commits and/or an open PR; include log onelines + shortstat |
| `skipped` | Default branch; GitHub-protected when detectable; compare failures |

Protected-branch detection is best-effort (`gh api …/branches/<name>`). If
unknown, treat as normal and report push-delete failures.

### 4. CLI helper: `issue-flow agent branches [--json]`

Read-only. Returns the three buckets so agents do not re-implement cherry/`gh`
logic. Skill documents a manual `git`/`gh` fallback when the CLI is missing.
Deletes and `gh issue create` stay in the skill (confirm-gated), not in the CLI.

### 5. Findings issue

Offer after the audit; show draft title/body; create only on yes. Suggested
title: `chore: remote branch audit (<YYYY-MM-DD>)`. Does not go through
`/iflow-issue` (different intent: audit dump vs authored spec).

## Alternatives considered

- Report-only v1 (no remote delete) — rejected; issue asked for deletable
  checks plus action under confirm.
- Skill-only without CLI (#172-style defer) — rejected; classification is
  mechanical and benefits from stable JSON like `preflight` / `doctor`.
- Fold remote deletes into Phase A confirm — rejected; too easy to consent
  to remote deletes accidentally when cleaning locals.

## Link

Issue #163, `issue163_plan.md`.
