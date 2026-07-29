# Plan: Issue #220 — utilizing gh for finding out when CI is green

## Goal

Make agents reliably discover and use GitHub CLI commands to wait on / report CI
(`gh pr checks [--watch]`, plus `gh run list` / `gh run watch` as fallback), not
only buried inside `/iflow-close` yolo wording.

## Constraints

- Templates under `src/issue_flow/templates/` are source of truth; edit those,
  then re-render via `issue-flow update` (do not hand-edit `.cursor/` copies as
  the fix).
- Honour [#172](../04-designs-and-guides/gh-list-and-watch.md): **`gh pr checks`
  / `gh pr checks --watch --fail-fast` stay primary** for PR-attached CI; "CI
  green" = exit 0. Always pass `--repo <owner/repo>`.
- Reuse existing `[issueflow].checks_watch_minutes` (default 15) — no second
  budget knob.
- No new `issue-flow agent` watch subcommand (deferred again in #172).
- Skill authoring rules in
  [skill-authoring.md](../04-designs-and-guides/skill-authoring.md): lifecycle
  skills stay user-invoked; only model-invoked skills get trigger-rich
  descriptions.
- Do not re-litigate yolo merge order already shipped in #172.

### Prior art

- [#172](../03-solved-issues/issue172_plan.md) +
  [gh-list-and-watch.md](../04-designs-and-guides/gh-list-and-watch.md): close /
  yolo already teach `gh pr list` + `gh pr checks [--watch]` with
  `checks_watch_minutes`; design doc allowed `gh run list` / `gh run watch`
  only as fallback when PR checks are empty — **that fallback is not named in
  templates today**.
- Close / yolo / docs / rules mention `gh pr checks` only in the close path;
  build early-PR lists/creates drafts but does not teach waiting on CI.
- Model-invoked skill precedent: `caveman`, `grill-me` (trigger-rich
  `description`, no `disable-model-invocation`).
- Config / bake: `resolve_checks_watch_minutes` in `config.py`, template var
  `checks_watch_minutes`.
- Toolbox: nothing CI-related (`verify_scaffold.py` only).
- Graph: close / HISTORY / gh-list-and-watch community.

## Approach

1. **New model-invoked Agent Skill `gh-ci`** (stem `gh_ci`)  
   Short cheatsheet agents can auto-attach when waiting on CI:
   - Primary: `gh pr checks <n> --repo <owner/repo>` (snapshot) and
     `gh pr checks <n> --repo <owner/repo> --watch --fail-fast` (wait),
     wall-clock cap **`{{ checks_watch_minutes }}`** minutes (agent-enforced).
   - Fallback when PR checks are empty / unavailable: `gh run list --repo …`
     then `gh run watch <run-id> --repo …` (this is the command the issue
     names).
   - Exit semantics: green = checks exit 0; red → stop and report failing
     check/run URLs; never hang past the budget.
   - Trigger-rich `description` (model-invoked); **not** a lifecycle slash
     command — no `commands/iflow-*.md.j2` twin.
   - Include in standard mode skill set (`SKILL_DIRS` / mode defaults).

2. **Wire discoverability into existing surfaces** (pointers, not dumps)  
   - `/iflow-close` skill + command: one line pointing at `gh-ci` for the
     checks toolkit; keep the concrete merge/watch steps in close (behavior
     stays there).
   - Always-on rules body: one short "CI via gh" bullet under external CLIs /
     close notes so agents see it outside close.
   - Optional one-liner in `docs/issue-workflow.md.j2`.

3. **Extend design doc**  
   Update `gh-list-and-watch.md` (or add a short sibling) recording: #220 adds
   the `gh-ci` skill + names `gh run *` fallback; #172 decisions unchanged.

4. **Out of scope**  
   - Changing yolo merge / `--auto` last-resort policy.  
   - New config keys.  
   - Teaching browser Actions UI.  
   - Auto-running watches from `/iflow-build` (early draft PR stays create-only).

## Files to touch

| Path | Change |
|------|--------|
| `src/issue_flow/templates/skills/gh_ci/SKILL.md.j2` | New model-invoked CI/`gh` cheatsheet |
| `src/issue_flow/templating.py` | Register `gh_ci` in `SKILL_DIRS` |
| `src/issue_flow/modes.py` | Include `gh_ci` in standard (and any mode that ships close) |
| `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2` | Pointer + name `gh run list` / `gh run watch` fallback |
| `src/issue_flow/templates/commands/iflow-close.md.j2` | Same |
| `src/issue_flow/templates/rules/_body.md.j2` | Short always-on CI/`gh` bullet |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Optional one-liner |
| `.issueflows/04-designs-and-guides/gh-list-and-watch.md` | Record #220 extension |
| `tests/test_templating.py` (and modes/init tests if needed) | Assert skill renders, ships in mode, mentions `gh run watch` + `gh pr checks` |

## Test strategy

- `uv run pytest` — new skill present in scaffold; description triggers;
  rendered close + skill mention `gh pr checks` and `gh run watch`; baked
  minutes still present.
- `uv run .issueflows/00-tools/verify_scaffold.py` if template/mode set changes
  warrant it.
- `uv run ruff check src/ tests/`.
- No live `gh` / Actions integration tests.

## Open questions

1. **Surface shape** — **Recommended: new model-invoked `gh-ci` skill** (+ thin
   pointers in close/rules). Alternative: rules-only / close-only expansion
   (smaller diff, weaker discoverability when not in close).
2. **Command primacy** — **Recommended: keep #172** (`gh pr checks` primary,
   `gh run *` named fallback). Alternative: elevate `gh run watch` to
   first-class equal (diverges from #172 design doc).
