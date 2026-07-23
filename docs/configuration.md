# Configuration

issue-flow reads settings from two places:

- **`.env`** (project root, via python-dotenv) — machine/user-level defaults.
- **`.issueflows/config.toml`** — the project's persisted choices. Persisted
  values deliberately **beat** the environment, so a stray env var can't
  silently override your project's configuration on `update`.

## Environment variables (`.env`)

`issue-flow init` **creates a starter `.env` when one is missing** (all
`ISSUEFLOW_*` lines written commented-out, so nothing is overridden until you
uncomment). It never replaces an existing `.env` — not even with `--force`; on
later runs it only *appends* commented hints for any `ISSUEFLOW_*` keys you
don't already have. `issue-flow update` does not touch `.env` at all.

| Variable                 | Default        | Description |
| ------------------------ | -------------- | ----------- |
| `ISSUEFLOW_DIR`          | `.issueflows`  | Name of the issue-tracking directory. |
| `ISSUEFLOW_EDITOR`       | `cursor`       | Default editor profile when `--editor` is not passed (`cursor`, `claude`, `opencode`, `codex`). |
| `ISSUEFLOW_AGENT_DIR`    | *(per editor)* | Override the agent/IDE config directory. When unset it is derived from the editor profile (e.g. `.cursor`, `.claude`, `.opencode`, `.codex`). |
| `ISSUEFLOW_DOCS_DIR`     | `docs`         | Where to write the workflow documentation file. |
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md`   | Changelog file that `/iflow-close` updates (set to e.g. `CHANGELOG.md` for different conventions). |
| `ISSUEFLOW_MODE`         | `standard`     | Fallback [scaffolding mode](#modes) when none is persisted in `config.toml`. Full order: `--mode` (CLI) > `config.toml` > `ISSUEFLOW_MODE` > `standard`. |
| `ISSUEFLOW_SKILL_LEVEL`  | `standard`     | Fallback [skill level](#skill-levels) when none is persisted in `config.toml`. Full order: `--skill-level` (CLI) > `config.toml` > `ISSUEFLOW_SKILL_LEVEL` > `standard`. |
| `ISSUEFLOW_CAVEMAN_DEFAULT` | `false`     | Fallback for the [always-on caveman](#caveman-skill) toggle. Full order: `config.toml` > `ISSUEFLOW_CAVEMAN_DEFAULT` > `false`. Only honored when the `caveman` skill is in the active mode. |
| `ISSUEFLOW_GRILL_ME_DEFAULT` | `false`    | Fallback for the [grill-me-during-planning](#grill-me-skill) toggle. Full order: `config.toml` > `ISSUEFLOW_GRILL_ME_DEFAULT` > `false`. Only honored when the `grill_me` skill is in the active mode. |
| `ISSUEFLOW_LABEL_FLOWS`  | `true`         | Fallback for the [label-driven flows](#label-driven-flows) toggle. Full order: `config.toml` > `ISSUEFLOW_LABEL_FLOWS` > `true`. Only honored when the `iflow-pick` and `iflow-yolo` commands are in the active mode. |
| `ISSUEFLOW_YOLO_LABEL`   | `yolo`         | Fallback for the [yolo trigger label](#label-driven-flows). Full order: `config.toml` > `ISSUEFLOW_YOLO_LABEL` > `yolo`. |
| `ISSUEFLOW_LINGUIST_ATTRIBUTES` | `false` | Fallback for the [Linguist `.gitattributes`](#linguist-gitattributes) toggle. Full order: `config.toml` > `ISSUEFLOW_LINGUIST_ATTRIBUTES` > `false` (opt-in). |

The optional [graphify integration](graphify.md) additionally reads an LLM API
key (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`MOONSHOT_API_KEY`) from `.env` for its semantic `extract` pass.

## Creating `config.toml`

`init --mode <id>` is the usual way `.issueflows/config.toml` first appears, but
you can also materialize a fully-commented file on demand:

```bash
issue-flow config add            # create .issueflows/config.toml if missing
issue-flow config add --force    # regenerate its [issueflow] keys in place
```

It writes the keys issue-flow actually reads from `config.toml` — `mode`,
`skill_level`, `caveman_default`, `grill_me_default`, `label_flows`,
`yolo_label`, `checks_watch_minutes`, `step_directives`, `model_label_flows`,
`deep_model_label`, `fast_model_label`, `linguist_attributes`,
`remind_cleanup`, `suggest_graphify`, `auto_switchback`, `pr_merge_method`,
`cycle_max_issues`, `confirm_version_bump`, `ruff_autofix`, `auto_close`,
`confirm_changelog_update` — taking each value from its `ISSUEFLOW_*` env var / `.env`
when set, otherwise the issue-flow default.
The other `ISSUEFLOW_*` settings are **environment-only** and are deliberately
*not* written to `config.toml` (putting them there would have no effect). An
existing file is left untouched unless `--force` is passed, in which case the
keys are upserted while your comments and `[modes.*]` tables are preserved.
After changing any of these keys, re-run `issue-flow update` so the rule and
commands re-render (and so optional side effects like the Linguist
`.gitattributes` block can apply). Pass `--json` for a machine-readable result.

## Modes

A **mode** selects which workflow surfaces (skills / slash commands) `init`
installs, so you can scaffold a lighter workflow when the full lifecycle is more
than you need. Two modes ship built in:

| Mode | What you get |
| --- | --- |
| `standard` (default) | The full workflow: planning, PRs, history, cleanup, graphify, and all helpers. |
| `simple` | A markdown-only lifecycle (capture, plan, implement, park, status, archive). No PR/cleanup/yolo/fix/graphify automation. Includes `/iflow-archive` for condensing a large `03-solved-issues/` folder. |

```bash
issue-flow init --mode simple
```

The chosen mode is **persisted** to `.issueflows/config.toml`
(`[issueflow].mode`), so `issue-flow update` refreshes exactly that mode's
surfaces. `update` never changes the mode — switch by re-running `init --mode
<id>` (which also prunes the surfaces the new mode drops). The active mode
resolves in this order: **`--mode` (CLI, on `init`)** > **`config.toml`**
(the persisted choice) > **`ISSUEFLOW_MODE`** (env, a fallback for projects that
haven't persisted a mode) > **`standard`**.

### Custom modes

A project can define its own modes in `.issueflows/config.toml` using
`[modes.<id>]` tables — either explicit `skills`/`commands` lists or `extends`
+ `add`/`remove` to compose on top of a built-in mode (a mode may reference any
surface issue-flow ships):

```toml
[issueflow]
mode = "mine"

[modes.mine]
name = "Mine"
extends = "simple"
add = ["iflow_graphify"]
```

## Skill levels

A **skill level** controls how opinionated the scaffolded quality-tooling
guidance is. It is set with `init --skill-level <level>`, persisted to
`.issueflows/config.toml` (`[issueflow].skill_level`), and honoured by
`update`:

| Level | What you get |
| --- | --- |
| `basic` | Minimal guidance; no extra tooling documents. |
| `standard` (default) | The regular workflow guidance; no extra tooling documents. |
| `advanced` | Additionally writes `.issueflows/04-designs-and-guides/python-quality-tools.md` — opinionated (and explicitly advisory) recommendations for type checking (mypy/pyright), linting and formatting (ruff), pre-commit hooks, and pytest coverage. Agents are instructed to **ask before** installing or configuring any of it, and to run `ruff check --fix` / `ruff format` before `/iflow-close` when the project already uses ruff. |

Resolution order mirrors modes: `--skill-level` (CLI) > `config.toml` >
`ISSUEFLOW_SKILL_LEVEL` (env) > `standard`.

## Multi-editor teams (canonical format)

When teammates use different AI coding tools (Cursor, Claude Code, opencode,
Codex), issue-flow can keep a **team-committed canonical store** under
`.issueflows/agent/` (portable `SKILL.md` snapshots + `manifest.json`) plus the
shared `AGENTS.md` managed block. Per-editor trees (`.cursor/`, `.claude/`, …)
are generated locally and can be gitignored.

```bash
# Team setup: commit .issueflows/agent/ instead of every editor tree
issue-flow init --canonical

# After checkout: materialize your local editor surfaces
issue-flow convert --to cursor          # or claude, opencode, codex

# Before push: refresh canonical store and drop local editor trees
issue-flow convert --to canonical --prune-other
```

Persisted keys in `config.toml`:

| Key | Purpose |
| --- | --- |
| `canonical_format = true` | Project uses the canonical store in git (set by `init --canonical` or `convert --to canonical`). |
| `editor = "cursor"` | Last local editor target for `convert` (optional; `ISSUEFLOW_EDITOR` still wins when set). |

`init --canonical` also appends a managed `.gitignore` block for local editor
directories. Re-run with `issue-flow convert --gitignore` if you adopted the
workflow later.

Git hooks for automatic pull/push conversion are planned as a follow-up (#23
phase 2 / #101-adjacent); hooks remain opt-in.

## Caveman skill

The `standard` mode installs an optional `caveman` Agent Skill
(`<agent_dir>/skills/caveman/`) — a terse, "token-greedy" response style
that keeps technical substance but drops filler. It is off by default and only
activates when you ask for it ("caveman" / "token greedy"); turn it off with
"stop caveman" or "normal mode". The lightweight `simple` mode omits it.

To make caveman **on by default for a project**, set `caveman_default = true`
under `[issueflow]` in `.issueflows/config.toml` and re-run `issue-flow update`:

```toml
[issueflow]
caveman_default = true
```

This renders an always-on caveman pointer into the managed rule body (so the
always-applied rule re-arms it every session); you can still drop it for the rest
of a session with "stop caveman" / "normal mode". The flag is only honored when
the `caveman` skill is part of the active mode.

## Grill-me skill

The `standard` mode also installs a `grill-me` Agent Skill
(`<agent_dir>/skills/grill-me/`) — a relentless planning interview that
stress-tests a plan or design (one question at a time, each with a recommended
answer) until every branch of the decision tree is resolved, then feeds the
conclusions into `issue<N>_plan.md`. It is off by default and only activates when
you ask for it ("grill me"); turn it off with "stop grilling" or "normal mode".
The lightweight `simple` mode omits it.

To make grilling **on by default during planning for a project**, set
`grill_me_default = true` under `[issueflow]` in `.issueflows/config.toml` and
re-run `issue-flow update`:

```toml
[issueflow]
grill_me_default = true
```

This renders an always-on grill-me pointer into the managed rule body and the
`/iflow-plan` skill, so planning starts with a grilling pass every session; you
can still drop it for the rest of a session with "stop grilling" / "normal mode".
The flag is only honored when the `grill_me` skill is part of the active mode.

## Label-driven flows

Issue labels can select the flow: when an issue picked via `/iflow-pick`
carries the **`yolo`** label, it is routed through the hands-off `/iflow-yolo`
chain (one combined confirmation covering the branch and the whole
`init → plan → build → close yolo` run, which merges the PR and pulls the
default branch at the end). This is **on by default** and controlled by two
keys under `[issueflow]` in `.issueflows/config.toml`:

```toml
[issueflow]
label_flows = true    # allow labels to select the flow (default: true)
yolo_label = "yolo"   # the label that triggers the yolo flow (default: "yolo")
```

Set `label_flows = false` to opt out, or change `yolo_label` to use a different
trigger label; re-run `issue-flow update` after changing either so the commands
re-render. Only honored when the `iflow-pick` and `iflow-yolo` commands are part
of the active mode.

Related off-path flows (see [The workflow](issue-workflow.md)):

- `/iflow-review` — propose which open issues should get the configured
  `yolo_label` (re-score all open issues; apply behind one confirm).
- `/iflow-cycle yolo` — alias for `label:<yolo_label>`; batch-process every
  open issue that carries that label under one up-front confirm.

## Linguist `.gitattributes`

Optionally keep GitHub Linguist language stats focused on library source by
writing a managed root `.gitattributes` block (marks `graphify-out/` as
generated and docs / tests / `.issueflows/` / `scripts/` / `dev/` as
documentation). This is **off by default** (opt-in):

```toml
[issueflow]
linguist_attributes = true
```

Re-run `issue-flow update` (or `init`) after enabling. The writer is
idempotent: it appends a `# BEGIN issue-flow linguist` … `# END` marker block
once and never rewrites user rules outside those markers. Turning the flag
back to `false` leaves an existing managed block in place (no auto-delete).

## Skill-behaviour knobs

Lifecycle skills can be tuned with additional `[issueflow]` keys (baked at
`issue-flow update`; same precedence as other toggles):

| Key | Default | Effect |
| --- | --- | --- |
| `remind_cleanup` | `true` | Remind the user to run `/iflow-cleanup` after close / cycle / dispatcher state D |
| `suggest_graphify` | `true` | Soft-suggest skimming `GRAPH_REPORT.md` / rebuilding graphify (never auto-runs) |
| `auto_switchback` | `true` | After `/iflow-close` opens a PR, switch to the default branch when clean (`false` ≈ always `stay`) |
| `pr_merge_method` | `"squash"` | Yolo close merge flag: `squash`, `merge`, or `rebase` |
| `cycle_max_issues` | `10` | Default `/iflow-cycle` queue safety cap (raise per run with `max:<n>`) |
| `auto_adversarial_loops` | `2` | Default `/iflow-auto` inter-epoch adversarial loop budget (override per run with `loops:<n>`) |
| `confirm_version_bump` | `false` | When `true`, non-yolo close asks once about a version bump if none was requested |
| `ruff_autofix` | `true` | When ruff is present, run `ruff check --fix` + `ruff format` from start/close |
| `auto_close` | `false` | When `true`, `/iflow-build` (and `/iflow-fix` end) chain into `/iflow-close` when work is ready to ship; close keeps its own confirms |
| `early_pr` | `false` | When `true`, `/iflow-build` opens a draft PR after the first push; trailing `early` / `pr` / `noearly` override per run |
| `confirm_changelog_update` | `false` | When `true`, `/iflow-close` shows the changelog diff and confirms once before writing (decline **stops** close); `false` writes without asking so the bullet lands in the PR (`nohistory` still skips) |

```toml
[issueflow]
remind_cleanup = true
suggest_graphify = true
auto_switchback = true
pr_merge_method = "squash"
cycle_max_issues = 10
auto_adversarial_loops = 2
confirm_version_bump = false
ruff_autofix = true
auto_close = false
early_pr = false
confirm_changelog_update = false
```

Env fallbacks: `ISSUEFLOW_REMIND_CLEANUP`, `ISSUEFLOW_SUGGEST_GRAPHIFY`,
`ISSUEFLOW_AUTO_SWITCHBACK`, `ISSUEFLOW_PR_MERGE_METHOD`,
`ISSUEFLOW_CYCLE_MAX_ISSUES`, `ISSUEFLOW_AUTO_ADVERSARIAL_LOOPS`,
`ISSUEFLOW_CONFIRM_VERSION_BUMP`, `ISSUEFLOW_RUFF_AUTOFIX`,
`ISSUEFLOW_AUTO_CLOSE`, `ISSUEFLOW_EARLY_PR`,
`ISSUEFLOW_CONFIRM_CHANGELOG_UPDATE`. Re-run `issue-flow update` after changing any of
these so skills and rules re-render.
