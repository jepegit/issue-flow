# Skill-behaviour knobs

**Context.** Issue #182: templates + `config.toml` already bake toggles
(`caveman_default`, `label_flows`, `checks_watch_minutes`, …). More knobs
should tweak lifecycle *nudges* and close/yolo/cycle parameters without editing
templates by hand.

**Decision.** `[issueflow]` keys, same precedence as siblings
(`project config.toml` > user-global `config.toml` > `ISSUEFLOW_*` env >
default), baked at `issue-flow update`. User-global path and lock
semantics: [user-global-config.md](./user-global-config.md) (issue #281 /
epic #269). Until Stage 2 ships, only the project file and env exist.

**Naming conventions** (after consistency pass):

| Pattern | Keys |
|---------|------|
| Soft nudges (`verb_object`) | `remind_cleanup`, `suggest_graphify` |
| Named help mode | `noob` (issue #307; distinct from scaffolding `--mode novice`) |
| Cleanup defaults (`cleanup_*`) | `cleanup_include_github`, `cleanup_yes_a1`, `cleanup_yes_a2` |
| Tool upgrade (event-hook name) | `on_bleeding_edge` |
| Auto behaviours (`auto_*`) | `auto_switchback`, `auto_remove_worktree`, `auto_close`, `auto_cleanup`, `auto_plan`, `auto_build`, `auto_graphify_on_plan` |
| Start layout | `worktree_first` (issue #329; distinct from `auto_remove_worktree` and from worktree location #328) |
| Timing / PR | `early_pr` |
| Fix-session | `fix_auto_name` |
| Auto / advanced | `auto_adversarial_loops` (see [advanced-auto-mode.md](./advanced-auto-mode.md)) |
| Confirm gates (`confirm_*`) | `confirm_version_bump`, `confirm_changelog_update` |
| Changelog write timing | `defer_changelog` |
| Tool / value | `ruff_autofix`, `pr_merge_method`, `cycle_max_issues`, `cycle_onfail`, `cycle_nonyolo`, `test_runner`, `essential_marker`, `essential_review` |
| Feature masters (`*_tests` / paradigm) | `essential_tests` |
| Per-repo skip (`locked`) | `locked` (project `config.toml` only; `update --all` skips) |

| Key | Default | Effect |
|-----|---------|--------|
| `remind_cleanup` | `true` | Soft reminders to run `/iflow-cleanup` after close / cycle / iflow-D (never auto-run). `false` = no in-flow nudges; cleanup only via explicit `/iflow-cleanup` (issue #233) |
| `noob` | `false` | After each lifecycle step, print recommended next from `issue-flow agent state` (focus → `next_command`; no-focus epic gap → `epic_session` + `epic_hint`, not raw `next_command`) plus a short relevant `/iflow-*` list. Never auto-dispatch. Seeded `true` on first-time `--mode novice` only (issues #307, #337) |
| `cleanup_include_github` | `false` | When `true`, `/iflow-cleanup` runs Phase B (GitHub remote audit) by default; trailing `no github` / `local only` opts out (issue #233) |
| `cleanup_yes_a1` | `false` | When `true`, Phase A1 runs without a yes/no (the action list is still printed). Trailing `ask a1` forces the prompt. Does not authorize A2 (issue #388) |
| `cleanup_yes_a2` | `false` | When `true`, Phase A2 `git branch -D` runs without a yes/no (names and tip SHAs still printed). Trailing `ask a2` forces the prompt. `issue-flow update` warns while this is on. Never deletes `unique_work` (issue #388) |
| `on_bleeding_edge` | `false` | When `true`, `/iflow-cleanup` runs `issue-flow agent self-update` after a successful FF pull (`uv tool install issue-flow@latest` then `issue-flow update`). Trailing `bleeding edge` / `no bleeding` override. Skips editable installs (issue #382) |
| `suggest_graphify` | `true` | Soft GRAPH_REPORT / rebuild suggestions (never auto-run) |
| `auto_graphify_on_plan` | `false` | `/iflow-plan` runs `issue-flow graphify` (AST `update`) before prior-art; missing/fail → note + continue (issue #214) |
| `auto_switchback` | `true` | After PR, switch to default when clean (`false` ≈ always `stay`) |
| `auto_remove_worktree` | `true` | After `/iflow-close` opens or merges a PR, remove the sibling issue worktree when clean (`false` = YES/NO). Skip `stay` / draft / failed merge. Never deletes the branch (issue #273) |
| `worktree_first` | `true` | `/iflow-pick` / `/iflow-issue` / `/iflow-fix` start in a sibling worktree. `false` → `git switch -c` on home. Tokens `inplace` / `no worktree` / `worktree` override (issue #329) |
| `auto_close` | `false` | `/iflow-build` / `/iflow-fix` end chain into `/iflow-close` when ready |
| `auto_cleanup` | `false` | After a PR exists, watch until it merges (`checks_watch_minutes`) and then run `/iflow-cleanup`. Does not merge. Independent of `auto_close` (issue #388) |
| `auto_plan` | `true` | `/iflow-pick` chains into `/iflow-plan` after pick confirm + branch/init; trailing `noplan` skips once (issue #219) |
| `auto_build` | `true` | `/iflow-plan` chains into `/iflow-build` on plan Accept; trailing `nobuild` skips once (issue #219) |
| `early_pr` | `false` | `/iflow-build` opens a draft PR after the first push; trailing `early`/`pr` / `noearly` override per run |
| `fix_auto_name` | `false` | `/iflow-fix` invents session title/slug without a naming confirm; create issue+branch still confirms (issue #258). CLI: `issue-flow config show\|set\|edit` |
| `auto_adversarial_loops` | `2` | `/iflow-auto` inter-epoch adversarial loop budget; trailing `loops:<n>` overrides per run ([advanced-auto-mode.md](./advanced-auto-mode.md)) |
| `confirm_version_bump` | `false` | Non-yolo close confirms once about bump when unset |
| `confirm_changelog_update` | `false` | Changelog diff confirm before write; `false` = write without ask (bullet lands in the PR). Decline (when true) **stops** close — no silent skip. |
| `defer_changelog` | `false` | When `true`, issue branches never write `HISTORY.md` / CHANGELOG; the bullet is recorded on `issue<N>_status.md` + PR body and applied on the default branch after merge (`issue-flow agent apply-changelog`). Default off keeps today's #171 / #240 / #260 path. |
| `pr_merge_method` | `"squash"` | Yolo `gh pr merge --{squash\|merge\|rebase}` |
| `cycle_max_issues` | `10` | `/iflow-cycle` safety cap before `max:<n>` |
| `cycle_onfail` | `"stop"` | Default `/iflow-cycle` failure policy (`stop` \| `skip`); per-run `onfail:` token overrides (issue #248) |
| `cycle_nonyolo` | `"merge"` | Non-yolo lane merge policy for `yolo: no` issues in cycle / auto / drive (`merge` \| `pr-only` \| `stop`); per-run `nonyolo:` token overrides; env `ISSUEFLOW_CYCLE_NONYOLO` (issue #386) |
| `ruff_autofix` | `true` | Gate ruff `--fix` / format in start/close |
| `essential_tests` | `false` | Opt-in essential-suite paradigm (pytest); see [essential-tests.md](./essential-tests.md) (issue #213) |
| `test_runner` | `"pytest"` | Runner for essential-tests; v1 only `"pytest"` supported |
| `essential_marker` | `"essential"` | pytest mark name for the essential suite |
| `essential_review` | `"close"` | When to triage issue-touched tests: `close` \| `build` \| `both` \| `never` |
| `locked` | `false` | Per-repo skip for `issue-flow update --all`. Project `.issueflows/config.toml` only; user-global must not set it. Missing key = unlocked. Single-repo `update` still runs. Optional process override: `ISSUEFLOW_LOCKED`. See [user-global-config.md](./user-global-config.md) (issue #281) |

**Consistency.** `auto_plan` / `auto_build` / `auto_close` / `auto_cleanup` are **independent** —
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
`defer_changelog = true` moves only the **file write** to the default branch
after merge; the close-step *decision* (and the confirm gate) still runs.

**Continue to next step** (issue #388). Each knob only skips its own pause.
Cleanup cannot run until the PR is merged, so `auto_cleanup` watches and
does not merge.

| Step | Knob | Default |
| --- | --- | --- |
| Pick confirm | (always ask) | — |
| Capture | part of pick; no separate knob | — |
| Plan | `auto_plan` | `true` |
| Build | `auto_build` | `true` |
| Close | `auto_close` | `false` |
| Cleanup | `auto_cleanup` | `false` |

`cleanup_yes_a1` / `cleanup_yes_a2` are accept-knobs inside cleanup, not
continue-knobs. A1 does not authorize A2.

**Alternatives considered.**

- Runtime reads of `config.toml` by agents — rejected (matches
  [label-driven-flows.md](./label-driven-flows.md): bake at render time).
- Moving env-only path keys (`ISSUEFLOW_DIR`, …) into `config.toml` — out of
  scope; still environment-only.

**Link.** Issue #182.
