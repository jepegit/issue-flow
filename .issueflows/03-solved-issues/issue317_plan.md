# Plan: #317 Help agents watch until a PR is merge-ready

## Goal

Give agents one CLI answer for “can this PR merge yet?” — classify + optional
timed watch — without merging and without changing yolo’s merge sequence.

## Constraints

- Read-only vs the PR: no `gh pr merge`, no `--admin`, no skip-checks.
- Reuse `[issueflow].checks_watch_minutes` / `ISSUEFLOW_CHECKS_WATCH_MINUTES`
  (default 15) for `--watch`. Agent-enforced wall clock; `gh` has no cap.
- GitHub issue/PR numbers share a namespace; `N` is that number.
- Always pass `--repo <owner/repo>` (from resolve) on every `gh` call.
- Yolo still: try merge → `gh pr checks --watch` → retry → `--auto` last resort.

### Prior art

- `gh-ci` skill + close snapshot — checks only; no mergeability/review/draft
  (`src/issue_flow/templates/skills/gh_ci/SKILL.md.j2`, close templates).
- Design [gh-list-and-watch.md](../04-designs-and-guides/gh-list-and-watch.md)
  (#172 / #220): **deferred** “new `issue-flow agent` watch subcommand” —
  this issue lands that helper as **classify + poll**, not a replacement for
  yolo’s `gh pr checks --watch`.
- `_pr_needs_sync` / `run_pr_sync` — already reads `mergeable` +
  `mergeStateStatus` (`src/issue_flow/agent.py`). Coexist; do not fold
  `pr-ready` into `pr-sync` (sync mutates heads).
- `gitutils` `gh pr list` JSON already asks `mergeable,mergeStateStatus`.
- `00-tools/` — no CI/PR watcher.

## Approach

New **`issue-flow agent pr-ready [N]`**:

1. Resolve repo via existing `-C` / resolve path.
2. Fetch PR: `gh pr view <N> --repo <owner/repo> --json`
   `number,url,title,isDraft,state,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup`.
   If `N` omitted: `gh pr view --repo …` for the current branch; if none, exit 1
   `unknown` / note “no PR for this branch”.
3. Classify (first match wins):

   | `state` | When |
   | --- | --- |
   | `unknown` | `gh` missing, view failed, or empty payload |
   | `blocked` | closed; draft; `mergeable=CONFLICTING`; `mergeStateStatus` in `DIRTY` / `DRAFT`; `reviewDecision=CHANGES_REQUESTED`; any **required** check failed |
   | `pending` | `mergeable` empty/`UNKNOWN`; `mergeStateStatus` in `UNKNOWN` / `BLOCKED` / `BEHIND`; required check pending/queued; `reviewDecision=REVIEW_REQUIRED` |
   | `ready` | open, not draft, `mergeable=MERGEABLE`, `mergeStateStatus` `CLEAN` **or** `UNSTABLE` (optional-only noise), no required check failed/pending, review not `CHANGES_REQUESTED` / `REVIEW_REQUIRED` |

   Optional / unofficial checks (e.g. Cursor Approval Agent) must **not** block
   `ready`. Prefer `statusCheckRollup` + required flag when present; if GitHub
   omits required, treat `FAILURE` as blocked and `PENDING` as pending only
   when `mergeStateStatus` is `BLOCKED`/`UNKNOWN`, else ignore (UNSTABLE +
   MERGEABLE → `ready`).
4. JSON: `state`, `pr`, `url`, `title`, `isDraft`, `mergeable`,
   `mergeStateStatus`, `reviewDecision`, `pending_checks`, `failing_checks`,
   `notes`. Human text: one-line state + those fields + check names.
5. Exit **0** only when `state=ready`; **1** otherwise (including `--watch`
   timeout still `pending`).
6. **`--watch`:** loop classify + sleep (~15s, injectable) until `ready`,
   `blocked`, or budget elapsed. Do **not** call `gh pr checks --watch` here
   (one code path; yolo keeps that). Print last payload each iteration when
   not `--json`; `--json` emits once at the end.

Skills/docs (no merge behaviour change):

- `gh_ci`: prefer `issue-flow agent pr-ready [N] [--watch]` when the question
  is merge-ready; keep `gh pr checks` as the raw cheatsheet.
- `/iflow-close` non-yolo snapshot: after `gh pr checks`, **offer**
  `issue-flow agent pr-ready <n> --watch` (do not auto-run).
- `docs/cli.md` agent table + synopsis; `docs/llms.txt` +
  `docs/how-to/for-agents.md` one line.
- Update `gh-list-and-watch.md`: deferred agent watch is now `pr-ready`.

## Files to touch

- `src/issue_flow/agent.py` — `classify_pr_ready` + `run_pr_ready`
- `src/issue_flow/cli.py` — `agent pr-ready` command
- `src/issue_flow/gitutils.py` — thin `gh pr view` helper if none fits
- `tests/test_pr_ready.py` — mocked `gh` for ready / pending / blocked /
  missing / `--watch` timeout (no real sleep)
- `src/issue_flow/templates/skills/gh_ci/SKILL.md.j2`
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` +
  `commands/iflow-close.md.j2` (offer only)
- `docs/cli.md`, `docs/llms.txt`, `docs/how-to/for-agents.md`
- `.issueflows/04-designs-and-guides/gh-list-and-watch.md`

## Test strategy

`uv run pytest` — new unit tests with fake `gh` JSON (mirror `tests/test_pr_sync.py`).
No live GitHub. Optional CLI `--help` assertion like other agent commands.

## Open questions

None — UNSTABLE + optional pending = `ready` (matches how this repo already
merges). Say **Revise** if required-reviews-with-no-REVIEW_REQUIRED-field
should stay `pending` even when `mergeStateStatus=CLEAN`.
