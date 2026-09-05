# Status — Issue #243: `/iflow-cleanup` cannot prune squash-merged branches

- [x] Done

## What's done

**`gitutils`**

- `cherry_unique_count` / `unique_commit_onelines` / `unique_diff_shortstat`
  now take explicit refs. They hardcoded `origin/<x>`, so they could not
  compare a *local* branch at all; `run_branches` passes `origin/…` itself now.
- New: `list_local_branches`, `is_ancestor`, `branch_tip`, `delete_branch`,
  `gh_prs_by_head` (one batched `gh pr list` instead of one call per branch),
  `latest_unique_commit_date`, `parse_iso8601`.
- `unique_commit_onelines` gained `no_merges=True` so the listed subjects match
  what `git cherry` counts (it ignores merge commits).

**`agent local-branches`** (new, read-only, registered in `cli.py`)

Buckets each local branch as `reachable` / `squash_landed` /
`merged_pr_divergent` / `unique_work` / `skipped`, every entry carrying a `tip`
short SHA for recovery. Never deletes anything.

**`/iflow-cleanup` Phase A split**

- Step 4 classifies (CLI fast path + manual `git`/`gh` fallback).
- Phase A1: the old consolidated confirm, `-d` on `reachable` only.
- Phase A2 (new, separate confirm): `-D` for `squash_landed` /
  `merged_pr_divergent`, listing `<name> <tip>` plus the divergent branches'
  unique-commit subjects; tries `-d` first, falls back to `-D`. `unique_work`
  is never offered.
- Corrected the false "`-d` handles squash merges" claim in the cleanup skill +
  command, `rules/_body.md.j2` (both bullets), `docs/issue-workflow.md.j2`
  (pitfalls + cleanup section), the close skill's cleanup reminder, and the
  yolo skill/command `-D` guardrail (chains still never force-delete).

**Two findings that changed the design mid-build**

1. `git branch -d` accepts a branch merged into *its upstream* as well as HEAD,
   so it succeeds while `origin/<branch>` exists and only refuses after the PR
   merge + `fetch --prune` removes that ref. Phase A2 therefore tries `-d`
   first, and the test documents the pruned-ref state cleanup actually runs in.
2. A merged PR with differing commits has two causes: a squash rewrite (safe)
   or work pushed *after* the merge (must never be deleted). They are separated
   by comparing the newest unique commit's date to `mergedAt` — with parsed
   timestamps, since lexical ISO comparison mis-ranks `+02:00` against `Z` (the
   real `review-improvements` branch is off by 37 minutes).

**Tests / docs**

- New `tests/test_agent_local_branches.py`: temp repo with a real
  `git merge --squash`, covering all five buckets, tip SHAs, the `-d`-refuses
  premise, "never deletes", current-branch skipping, both merged-PR verdicts,
  and the missing-git exit.
- `tests/test_init.py`: three scaffold assertions (skill, command, rule + doc)
  pinning the A2 confirm and the removal of the old claim.
- `tests/test_cli.py`: remote-audit stubs updated for the new ref signatures.
- `docs/cli.md`: rows for `agent local-branches` **and** the previously
  undocumented `agent branches`.
- Design doc `04-designs-and-guides/local-branch-cleanup.md`, cross-linked from
  `github-branch-audit.md`.
- `uv run pytest`: 644 passed. `uv run ruff check src/ tests/`: clean.
  Scaffold re-rendered (`issue-flow update .`) and graph refreshed.

## Remaining work

- None for the issue itself. `HISTORY.md` bullet is `/iflow-close`'s step.
- Follow-up (deliberately out of scope): retrofit `run_branches` to the batched
  `gh_prs_by_head` — a behaviour-neutral speedup to already-shipped code.
- Dogfooding note: on this repo the classifier reports `review-improvements` as
  `merged_pr_divergent` (PR #127). Deleting it is an interactive
  `/iflow-cleanup` Phase A2 decision, not part of this issue.
