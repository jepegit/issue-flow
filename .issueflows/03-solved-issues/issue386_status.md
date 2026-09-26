# Status: #386 drive carries through under the overnight confirm

- [x] Done

## What's done

- Picked via `/iflow-pick` (2026-09-26). Worktree
  `/home/jepe/scripting/issue-flow-workspace/issue-flow-386`, branch
  `386-drive-carry-through`.
- Plan accepted (A–F, see `issue386_plan.md`); all parts built.

### F1 — root cause of every stale stamp

- `src/issue_flow/__init__.py`: `__version__` now resolved from
  `importlib.metadata` (was hard-coded `0.4.2a4`). Every rendered skill in
  this repo flipped from `issue-flow-version: 0.4.2a4` → `0.5.13` on the
  next `issue-flow update`. Guard: `tests/test_version.py` (essential).

### B — additive keep-both resolver

- `history.resolve_additive_conflict`: bullets **and** table rows, any
  position in the file, in-flight side last; refuses headings / prose /
  empty side. Tests in `tests/test_history.py`.

### C — `sync-branch` per-path resolver + stacked parent

- `agent._resolver_for_path`: changelog resolver for `HISTORY.md`, additive
  resolver for `<issueflows>/04-designs-and-guides/*.md` and
  `**/issue<N>_status.md`; payload `resolvers`. Product code still aborts.
- `agent sync-branch --base <ref>` → `git rebase --onto origin/<default>
  <ref>`; `_detect_stacked_base` auto-detects a provably landed ancestor
  branch (merged PR / zero cherry-unique / new `gitutils.content_landed`:
  touched files byte-identical upstream — the multi-commit squash case).
  Payload `base`, `base_detected`, `dropped_commits`.
- `gitutils`: `merge_base`, `content_landed`, `rev_list_count`,
  `rev_parse_verify`, `diff_name_only(paths=)`, `rebase_onto(base=)`.
- Tests: `tests/test_agent_sync_branch.py` (bookkeeping + stacked fixtures).

### A — non-yolo lane

- Knob `cycle_nonyolo` (`merge` | `pr-only` | `stop`, default `merge`, env
  `ISSUEFLOW_CYCLE_NONYOLO`, per-run token `nonyolo:<policy>`) wired through
  `modes.py`, `config.py`, `config_ops.py`, `docs/configuration.md`.
- `agent queue` payload: `nonyolo` list + `nonyolo_count`; text output
  marks `[non-yolo]` and prints the lane summary.
- Cycle skill/command: new **Lanes** section, confirm lists non-yolo issues,
  `cycle_status.md` records the policy, 6b widened to the bookkeeping set +
  stacked parents, 6c "not small" advisory on the non-yolo lane, "already
  merged" = success. Auto + drive forward `nonyolo:` and never stop at
  `yolo: no` unless the policy is `stop`.

### D/E — drive constraints + cleanup

- Drive: "never rebase / force-push / push" scoped to the **default branch**;
  issue branches sync via `sync-branch` + `--force-with-lease` as normal.
- Drive cleanup runs A1 **and** A2 under the drive confirm (cleanup token
  `drive` / `landed`): `-d` reachable, `-D` squash-landed (and
  merged-PR-divergent with nothing newer than `mergedAt`), never
  `unique_work`, tip SHAs printed, no Phase B.

### F2 — version drift surface

- `agent state` / `agent preflight`: `cli_version`, `skills_version` (from
  the rendered `iflow` skill's frontmatter), `version_drift` + note; `/iflow`
  prints one warning and continues (never runs `update` itself).

### Docs / guides

- `docs/cli.md`, `docs/configuration.md`, `docs/how-to/drive.md`,
  `docs/how-to/pr-sync.md`; `docs/issue-workflow.md` + all `.cursor/`
  skills re-rendered via `issue-flow update`.
- Design guides: `drive-mode.md` (carry-through section), `advanced-auto-mode.md`,
  `pr-queue-sync.md`, `skill-behaviour-knobs.md`, `test-registry.md`.
- `rules/_body.md.j2`: check `graphify-out/graph.json` before `graphify query`.

## Verification

- `uv run pytest` → 931 passed.
- `uv run ruff check src/ tests/` + `ruff format --check` → clean.

## Remaining work

- None for this issue. `/iflow-close` (optionally `bump`) to land.
