# gh list and watch in `/iflow-close`

**Context.** Issue #172: agents already depend on `gh` for PRs, but close said
"when CI is green" without naming commands, and yolo fell straight through to
`--auto` when checks were pending. Issue #220: agents still missed the toolkit
outside close wording and asked for `gh run watch` by name.

**Decision.**

- Interpret "gh list / gh watch" as **`gh pr list`** + **`gh pr checks [--watch]`**
  (no top-level `gh list` / `gh watch`). Always pass `--repo <owner/repo>`.
- **List before create:** after push, `gh pr list --head <branch> --state open`;
  reuse/update an existing open PR instead of opening a second one.
- **Checks snapshot** after the PR exists; "CI green" means `gh pr checks` exits 0.
- **Fallback** when PR checks are empty / unavailable: `gh run list` then
  `gh run watch <run-id>` (same watch budget). Named in close + the `gh-ci` skill.
- **Yolo merge:** try `gh pr merge --squash` first; on pending/required checks,
  `gh pr checks --watch --fail-fast` under a hard wall-clock budget, then retry
  merge. **`--squash --auto` is last resort** (cap elapsed, checks never
  register, or watch unavailable). Red checks stop hands-off.
- **Budget:** `[issueflow].checks_watch_minutes` (default `15`), env
  `ISSUEFLOW_CHECKS_WATCH_MINUTES`. Baked into close/yolo/`gh-ci` at
  `issue-flow update`. Agent-enforced (`gh` has no max-duration flag).
  Non-positive values fall back to the default.
- **Discoverability (#220):** ship a model-invoked **`gh-ci`** skill (standard
  mode; not simple) plus thin pointers in close and the always-on rules. Close
  still owns the merge sequence; `gh-ci` is the shared command cheatsheet.

**Alternatives considered.**

- Always `--auto` (status quo) — rejected: agents never see CI fail in-session.
- Open-ended watch — rejected: can hang unattended yolo/cycle runs.
- Promote a new `issue-flow agent` watch subcommand — deferred; shell `gh` is enough.
- Elevate `gh run watch` to equal primacy with `gh pr checks` — rejected (#220);
  keep #172 ordering.
- Rules-only / close-only expansion without a skill — rejected (#220); weaker
  discoverability when not already in close.

**Link.** Issues #172 / #220; `issue172_plan.md`, `issue220_plan.md`.
