# Issue #260 plan — Multi-PR HISTORY sync

## Goal

Stop open PRs from staying `DIRTY` after another merge (usually `HISTORY.md`), and give agents a skill/CLI to refresh a queue of PRs when it has already happened.

## Approach

### Part A — repair (`/iflow-pr-sync`) — ship first

1. **CLI** `issue-flow agent pr-sync`:
   - Inputs: optional PR numbers / `--all-open` / `--dirty-only` (default: open PRs that are behind or `mergeable: CONFLICTING`).
   - For each head: ensure worktree or temp checkout → run existing `sync-branch` logic → on success `git push --force-with-lease` (new explicit push path; never bare `--force`).
   - Abort that head on non-HISTORY / non-keep-both conflicts; continue or stop per flag (`--fail-fast` default true for safety).
   - `--json` + dry-run (`--dry-run`) listing planned actions without push.
2. **Skill** `iflow-pr-sync` (+ command): confirm list, run CLI or equivalent steps, report results; offer from cleanup/yolo when siblings remain.
3. **Tests**: unit/integration with mocked gh + temp repos; reuse history resolver cases.
4. **Design doc** `pr-queue-sync.md` linking `changelog-conflicts.md`.

### Part B — prevent (`defer_changelog`) — same PR if time, else follow-up commit

- Knob default `false`: when `true`, `/iflow-close` does not edit `HISTORY.md` on the issue branch; records bullet in status; `/iflow-cleanup` (or yolo post-pull) appends/promotes on default.
- Document bump: version promote only on default after merge.

## Non-goals

- Auto-merge the refreshed queue without confirm.
- Resolving code conflicts.
- Changing squash policy.

## Verification

- `uv run pytest` + ruff.
- Manual: two throwaway branches conflicting only on HISTORY → `pr-sync` refreshes second after first merges.
