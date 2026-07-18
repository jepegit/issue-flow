# Plan: Issue #172 — List and watch GitHub

## Goal

Teach `/iflow-close` (and the matching skill) to use GitHub CLI **list** and **watch** commands so agents reuse an open PR when one exists and wait on / report CI with `gh` instead of vague "when CI is green" wording — especially on the yolo merge path. Watch budget defaults to **15 minutes** and is **project-configurable**.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; edit those, not rendered `.cursor/` copies.
- Always pass `--repo <owner/repo>` (multi-root rule); never rely on `gh` cwd default.
- No top-level `gh list` / `gh watch` — interpret the issue as **`gh pr list`** + **`gh pr checks [--watch]`** (optional `gh run list` / `gh run watch` only as fallback when PR checks are empty).
- Config knobs follow existing pattern: `[issueflow]` in `.issueflows/config.toml` > `ISSUEFLOW_*` env > default; bake into templates at `init`/`update` (same as `yolo_label`). Re-run `issue-flow update` after changing.
- Watching stays agent/`gh` shell — no new `issue-flow agent` subcommand.
- Do not weaken yolo safeguards. Branch deletion still `/iflow-cleanup`.
- Existing tests assert `--squash --auto` in close/yolo surfaces — update those assertions deliberately.

### Prior art

- Close already uses `gh pr merge --squash` / `--squash --auto` (yolo) and cleanup uses `gh pr view` — no `gh pr list` or `gh pr checks` anywhere in templates today.
- Design decision in [label-driven-flows.md](../04-designs-and-guides/label-driven-flows.md): prefer immediate merge with `--auto` fallback over always-`--auto`. This issue refines that for pending checks.
- Config wiring precedent: `label_flows` / `yolo_label` in `config.py` + `modes.py` + `config add` + Jinja context (`resolve_*` → template vars).
- [agentic-cli.md](../04-designs-and-guides/agentic-cli.md): no new Python watch wrapper needed.
- Toolbox: nothing related. Graph: close / HISTORY communities.

## Approach

1. **PR step — list before create**  
   After push, before `gh pr create`:  
   `gh pr list --repo <owner/repo> --head <branch> --state open --json number,url,title,isDraft`  
   If a PR exists → update that PR instead of opening a second one.

2. **After PR — checks snapshot (all close paths)**  
   Run `gh pr checks <n> --repo <owner/repo>`. Report pass / fail / pending.  
   "CI is green" = this command exits 0 (or JSON buckets all `pass` / `skipping`).  
   Interactive close: one-shot list; offer `--watch` when user wants to wait. Still honour the configured cap (do not block forever).

3. **Yolo merge — watch then merge**  
   1. Try `gh pr merge <n> --squash`.
   2. If refused for pending/required checks: `gh pr checks <n> --repo … --watch --fail-fast` under a **hard wall-clock cap** of `{{ checks_watch_minutes }}` minutes (default **15**). `gh` has no max-duration flag — agent enforces the budget.
   3. Watch success within cap → retry `gh pr merge <n> --squash`.
   4. Watch red / fail-fast → stop hands-off, leave PR open, report failing check links.
   5. Cap elapses still pending, or checks never register / watch unavailable → `gh pr merge <n> --squash --auto`, report queued, continue switchback.
   6. `draft` still skips merge.

4. **Config knob** (new)  
   - Key: `checks_watch_minutes` under `[issueflow]` (integer minutes, default `15`).  
   - Env: `ISSUEFLOW_CHECKS_WATCH_MINUTES`.  
   - Resolution order: `config.toml` > env > `15`.  
   - Reject / clamp non-positive values to default (or fail validation on `config add` / write — match how other typed keys behave).  
   - Wire through: `modes.py` read/write + defaults, `config.py` `resolve_checks_watch_minutes`, template context, `issue-flow config add` seed + help text in `cli.py` / `agent.py` guide.  
   - Bake literal minutes into close/yolo skill + command templates (e.g. “watch at most **15** minutes”).

5. **Surfaces**  
   - Close skill + command (primary); short yolo cross-note.  
   - Design doc `gh-list-and-watch.md`.  
   - Optional one-liner in `docs/issue-workflow.md.j2`.  
   - Config/docs mentions where other `[issueflow]` keys are listed (AGENTS managed block / rules only if they already enumerate keys — prefer not expanding the always-on rule with every knob).

6. **Out of scope**  
   - New `issue-flow agent` watch subcommand.  
   - `/iflow-cleanup` / cycle merge changes.  
   - Browser flows; waiting on human review approvals.

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/modes.py` | Default + read/write `checks_watch_minutes` |
| `src/issue_flow/config.py` | `resolve_checks_watch_minutes` + template context + env seed |
| `src/issue_flow/cli.py` / `agent.py` | `config add` docs / hand-edit guide line |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | List / checks / watch-then-merge with baked minutes + `--auto` last resort |
| `src/issue_flow/templates/commands/iflow-close.md.j2` | Same |
| `src/issue_flow/templates/skills/iflow_yolo/SKILL.md.j2` | Cross-note watch budget / `--auto` |
| `src/issue_flow/templates/commands/iflow-yolo.md.j2` | Same |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Optional one-liner |
| Template for default `config.toml` (if any) | Seed key |
| `.issueflows/04-designs-and-guides/gh-list-and-watch.md` | Decision record (#172) |
| `tests/` (`test_templating.py`, config/modes tests) | Render asserts + resolve/default/override for the new key |

## Test strategy

- `uv run pytest` — close/yolo mention `gh pr list`, `gh pr checks`, `--watch`, baked minutes, `--auto` as last resort.
- Unit tests: default 15; `config.toml` override; env override; precedence.
- `uv run ruff check src/ tests/`.
- No live `gh` integration tests.

## Decisions (confirmed)

1. **Yolo CI strategy** — Watch-then-retry-merge; `--auto` when checks never appear, watch unavailable, or cap elapses while pending.
2. **Commands** — `gh pr list` + `gh pr checks [--watch]` as primary.
3. **Blocking duration** — Hard wall-clock cap, **default 15 minutes**, **configurable** via `[issueflow].checks_watch_minutes` / `ISSUEFLOW_CHECKS_WATCH_MINUTES`, baked at `issue-flow update`.

## Open questions

- None.
