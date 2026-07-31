# Skill-behaviour knobs

**Context.** Issue #182: templates + `config.toml` already bake toggles
(`caveman_default`, `label_flows`, `checks_watch_minutes`, …). More knobs
should tweak lifecycle *nudges* and close/yolo/cycle parameters without editing
templates by hand.

**Decision.** `[issueflow]` keys, same precedence as siblings
(`config.toml` > `ISSUEFLOW_*` env > default), baked at `issue-flow update`.

**Naming conventions** (after consistency pass):

| Pattern | Keys |
|---------|------|
| Soft nudges (`verb_object`) | `remind_cleanup`, `suggest_graphify` |
| Cleanup defaults (`cleanup_*`) | `cleanup_include_github` |
| Auto behaviours (`auto_*`) | `auto_switchback`, `auto_close`, `auto_plan`, `auto_build`, `auto_graphify_on_plan` |
| Timing / PR | `early_pr` |
| Auto / advanced | `auto_adversarial_loops` (see [advanced-auto-mode.md](./advanced-auto-mode.md)) |
| Confirm gates (`confirm_*`) | `confirm_version_bump`, `confirm_changelog_update` |
| Tool / value | `ruff_autofix`, `pr_merge_method`, `cycle_max_issues`, `test_runner`, `essential_marker`, `essential_review` |
| Feature masters (`*_tests` / paradigm) | `essential_tests` |

| Key | Default | Effect |
|-----|---------|--------|
| `remind_cleanup` | `true` | Soft reminders to run `/iflow-cleanup` after close / cycle / iflow-D (never auto-run). `false` = no in-flow nudges; cleanup only via explicit `/iflow-cleanup` (issue #233) |
| `cleanup_include_github` | `false` | When `true`, `/iflow-cleanup` runs Phase B (GitHub remote audit) by default; trailing `no github` / `local only` opts out (issue #233) |
| `suggest_graphify` | `true` | Soft GRAPH_REPORT / rebuild suggestions (never auto-run) |
| `auto_graphify_on_plan` | `false` | `/iflow-plan` runs `issue-flow graphify` (AST `update`) before prior-art; missing/fail → note + continue (issue #214) |
| `auto_switchback` | `true` | After PR, switch to default when clean (`false` ≈ always `stay`) |
| `auto_close` | `false` | `/iflow-build` / `/iflow-fix` end chain into `/iflow-close` when ready |
| `auto_plan` | `true` | `/iflow-pick` chains into `/iflow-plan` after pick confirm + branch/init; trailing `noplan` skips once (issue #219) |
| `auto_build` | `true` | `/iflow-plan` chains into `/iflow-build` on plan Accept; trailing `nobuild` skips once (issue #219) |
| `early_pr` | `false` | `/iflow-build` opens a draft PR after the first push; trailing `early`/`pr` / `noearly` override per run |
| `auto_adversarial_loops` | `2` | `/iflow-auto` inter-epoch adversarial loop budget; trailing `loops:<n>` overrides per run ([advanced-auto-mode.md](./advanced-auto-mode.md)) |
| `confirm_version_bump` | `false` | Non-yolo close confirms once about bump when unset |
| `confirm_changelog_update` | `false` | Changelog diff confirm before write; `false` = write without ask (bullet lands in the PR). Decline (when true) **stops** close — no silent skip. |
| `pr_merge_method` | `"squash"` | Yolo `gh pr merge --{squash\|merge\|rebase}` |
| `cycle_max_issues` | `10` | `/iflow-cycle` safety cap before `max:<n>` |
| `ruff_autofix` | `true` | Gate ruff `--fix` / format in start/close |
| `essential_tests` | `false` | Opt-in essential-suite paradigm (pytest); see [essential-tests.md](./essential-tests.md) (issue #213) |
| `test_runner` | `"pytest"` | Runner for essential-tests; v1 only `"pytest"` supported |
| `essential_marker` | `"essential"` | pytest mark name for the essential suite |
| `essential_review` | `"close"` | When to triage issue-touched tests: `close` \| `build` \| `both` \| `never` |

**Consistency.** `auto_plan` / `auto_build` / `auto_close` are **independent** —
each only skips its own next-step pause (pick confirm, plan Accept, and
build-ready still gate). Mode-gated on `iflow_plan` / `iflow_build` /
`iflow_close`. Do **not** imply yolo / auto-merge. One-shot skips: `noplan`,
`nobuild`. `auto_close` still honours `confirm_*`, `auto_switchback`,
`remind_cleanup`, `pr_merge_method`, etc.
`confirm_changelog_update = false` (default) matches yolo's no-prompt history
write so the bullet is always in the PR commit; `nohistory` still skips.
When confirm is on and declined, close **stops** (write / revise /
`nohistory` / abort) — never silent-skip and continue. Never offer a
HISTORY/CHANGELOG update after the PR is open or merged (see
[changelog-timing.md](./changelog-timing.md)).

**Alternatives considered.**

- Runtime reads of `config.toml` by agents — rejected (matches
  [label-driven-flows.md](./label-driven-flows.md): bake at render time).
- Moving env-only path keys (`ISSUEFLOW_DIR`, …) into `config.toml` — out of
  scope; still environment-only.

**Link.** Issue #182.
