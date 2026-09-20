# Plan: #321 Tighten pr-ready when required flags are omitted; CI on 3.12–3.14

## Goal

Stop `pr-ready` treating omitted-`isRequired` pending checks as optional noise
(the #320 false `ready`). Raise the tested/supported floor to Python 3.12–3.14.

## Constraints

- One PR, both deliverables (do not split).
- Do not change yolo’s `gh pr merge` / `gh pr checks --watch` sequence.
- Dev pin `.python-version` stays **3.13**. `publish.yml` stays on 3.13.
- Ignore pending/failing only when `isRequired` is **explicitly** `false`.

### Prior art

- `classify_pr_ready` / `_rollup_checks` in
  [`src/issue_flow/agent.py`](../../src/issue_flow/agent.py) (#317).
  Current omitted path: `block_pending = pending_all` only when
  `mergeStateStatus` is `BLOCKED`/`UNKNOWN`/`""` — that is the #320 bug.
- Tests: [`tests/test_pr_ready.py`](../../tests/test_pr_ready.py)
  (`test_classify_ready_unstable_optional_*`,
  `test_classify_omitted_required_failure_blocks`). Keep optional-explicit
  cases; add omitted-pending → `pending`.
- Design [gh-list-and-watch.md](../04-designs-and-guides/gh-list-and-watch.md):
  update the #317 “omitted required + UNSTABLE = ready” sentence.
- CI matrix: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).
- Toolbox: no CI/PR helper to reuse.
- Graph: `graph.json` absent in this worktree; skipped.

## Approach

1. **Unify check gating** in `classify_pr_ready`: a check counts as
   blocking (fail → `blocked`, in-flight → `pending`) unless
   `isRequired is False`. `True` and omitted (`None`) both count.
   Drop the `UNSTABLE` special-case that zeroed `block_pending`.
   Keep listing all pending/failing names in the payload; only the
   blocking subset drives `state`. Ready note “UNSTABLE with optional-only
   noise” only when remaining pending/failing are all explicit-optional.

2. **CI / metadata.** Matrix `["3.12", "3.13", "3.14"]`.
   `requires-python = ">=3.12"`; classifiers drop 3.11, add 3.14.
   Docs that claim 3.11+: `README.md`, `AGENTS.md` (package header).
   Fix stale `this-project.md` (says 3.13+) to 3.12+ / CI 3.12–3.14.
   Leave historical `HISTORY.md` 3.11 bullet; `docs/developing.md` is
   already “dev pin 3.13”. Do not touch scaffold templates’ 3.13 ruff pin.

## Files to touch

- `src/issue_flow/agent.py` — classify gate
- `tests/test_pr_ready.py` — omitted-pending UNSTABLE → `pending`; keep
  explicit-optional ready
- `.github/workflows/ci.yml` — matrix
- `pyproject.toml` — `requires-python` + classifiers
- `README.md`, `AGENTS.md`, `.issueflows/04-designs-and-guides/this-project.md`
- `.issueflows/04-designs-and-guides/gh-list-and-watch.md` — omitted-required rule

## Test strategy

`uv run pytest` + `uv run ruff check src/ tests/`. New unit case: UNSTABLE +
MERGEABLE + in-progress check with no `isRequired` → `pending`. Existing
Cursor-Approval `isRequired: false` + required success stays `ready`.

## Open questions

None — spec confirmed; no split.
