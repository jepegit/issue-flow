# Configuration

Most settings live in your project's `.issueflows/config.toml`, under
`[issueflow]`. Change one with `issue-flow config set` (or edit the file),
then run `issue-flow update` so the skills and rules pick it up:

```bash
issue-flow config set auto_plan false
issue-flow update
issue-flow config show            # every setting and its current value
```

A few settings are environment variables only (folder names, editor); see
[How settings are resolved](#how-settings-are-resolved) at the end.

## Common changes

| To … | Setting | Example |
| --- | --- | --- |
| Install fewer or more commands | `mode` | `issue-flow init --mode novice` (see [Modes](#modes)) |
| Stop after pick instead of going straight into planning | `auto_plan` | `issue-flow config set auto_plan false` |
| Stop after plan approval instead of starting the build | `auto_build` | `issue-flow config set auto_build false` |
| Work in your main checkout instead of a sibling worktree | `worktree_first` | `issue-flow config set worktree_first false` |
| Keep issue worktrees in one common folder | `worktrees_dir` | `issue-flow config set --global worktrees_dir ~/worktrees` |
| Get terse answers by default | `caveman_default` | `issue-flow config set caveman_default true` |
| Be interviewed about every plan | `grill_me_default` | `issue-flow config set grill_me_default true` |
| Stop labels from choosing the flow (yolo / ops) | `label_flows` | `issue-flow config set label_flows false` |
| Merge yolo PRs with a merge commit or rebase | `pr_merge_method` | `issue-flow config set pr_merge_method merge` |
| Get a "what next" hint after every step | `noob` | `issue-flow config set noob true` |

Run `issue-flow update` after any of these (`config set` reminds you).

## All settings

Every key `issue-flow config add` writes, with its default. Each key also has
an environment-variable fallback, `ISSUEFLOW_<KEY>` (for example
`ISSUEFLOW_AUTO_PLAN`), used when the key is not set in any `config.toml`.

| Key | Type | Default | Effect |
| --- | --- | --- | --- |
| `mode` | text | `"standard"` | Which commands are installed: `standard`, `novice`, `simple`, or a custom mode. Project only. See [Modes](#modes). |
| `skill_level` | text | `"standard"` | How opinionated the quality-tooling guidance is: `basic`, `standard`, `advanced`. See [Skill levels](#skill-levels). |
| `caveman_default` | bool | `false` | Terse caveman reply style on from the first message. See [Caveman skill](#caveman-skill). |
| `grill_me_default` | bool | `false` | Run the grill-me interview during every `/iflow-plan`. See [Grill-me skill](#grill-me-skill). |
| `label_flows` | bool | `true` | Let issue labels choose the flow in `/iflow-pick` (yolo → `/iflow-yolo`, ops → `/iflow-ops`). See [Label-driven flows](#label-driven-flows). |
| `yolo_label` | text | `"yolo"` | The label that routes an issue to `/iflow-yolo`; also what `/iflow-cycle yolo` and `/iflow-review yolo` use. |
| `ops_label` | text | `"ops"` | The label that routes an issue to `/iflow-ops` (ops wins over yolo). |
| `publish_label` | text | `"publish"` | Label that bumps + creates a GitHub release after merge (bare = patch; `publish:minor` / `publish:0.6.0` override). See [Label-driven flows](#label-driven-flows). |
| `checks_watch_minutes` | int | `15` | How long hands-off closes watch pending CI checks before falling back to `--auto` merge. |
| `step_directives` | bool | `true` | Add a MODEL & EXECUTION DIRECTIVE (economy or reasoning) to lifecycle skills; tune per step under `[issueflow.step_profiles]`. |
| `model_label_flows` | bool | `false` | Let `/iflow-pick` announce a deeper or faster model based on issue labels. |
| `deep_model_label` | text | `"deep"` | Label that asks for a reasoning-heavy model (with `model_label_flows`). |
| `fast_model_label` | text | `"fast"` | Label that asks for a fast, economical model (with `model_label_flows`). |
| `linguist_attributes` | bool | `false` | Write a managed `.gitattributes` block for GitHub language stats. See [Linguist](#linguist-gitattributes). |
| `pstack_skills` | list | `[]` | Opt-in vendored pstack skills: names such as `["unslop", "tdd"]`, or `"all"`. See [pstack skills](#pstack-skills). |
| `remind_cleanup` | bool | `true` | Remind you to run `/iflow-cleanup` after close / cycle (never runs it). `false` = no reminders. |
| `noob` | bool | `false` | End every lifecycle step with a recommended next command and a short list of relevant commands. Separate from `--mode novice`. |
| `cleanup_include_github` | bool | `false` | `/iflow-cleanup` also audits remote branches (Phase B) by default; opt out per run with `local only`. |
| `on_bleeding_edge` | bool | `false` | `/iflow-cleanup` upgrades the `uv tool` install to `issue-flow@latest` and runs `issue-flow update` after a successful fast-forward pull. Opt in per run with `bleeding edge`; opt out with `no bleeding`. Skips editable installs. |
| `suggest_graphify` | bool | `true` | Suggest reading `GRAPH_REPORT.md` / rebuilding graphify (never runs it). |
| `auto_graphify_on_plan` | bool | `false` | `/iflow-plan` rebuilds the graphify graph (AST only) before prior-art discovery. |
| `auto_switchback` | bool | `true` | After `/iflow-close` opens a PR, switch back to the default branch when the tree is clean (`false` ≈ always `stay`). |
| `auto_remove_worktree` | bool | `true` | Close removes the issue's sibling worktree once the PR is open (or merged) and the tree is clean; `false` asks first. |
| `worktree_first` | bool | `true` | `/iflow-pick`, `/iflow-issue` and `/iflow-fix` start in a sibling worktree `../<repo>-<N>`; `false` uses `git switch -c` in your checkout. Tokens `inplace` / `worktree` override per run. |
| `worktrees_dir` | text | `""` | Common folder for issue worktrees, e.g. `~/worktrees` (absolute or `~`). Empty = next to the repo. A missing folder or a relative path falls back to next-to-repo with a note. Best set user-wide (`--global`). See [Where the worktree goes](how-to/worktrees.md#where-the-worktree-goes). |
| `worktrees_in_workspace` | bool | `true` | When the repo sits in a workspace folder (an `issueflow-workspace.toml` above it), keep its worktrees next to it, inside that folder, even if `worktrees_dir` is set. |
| `pr_merge_method` | text | `"squash"` | How hands-off closes merge: `squash`, `merge`, or `rebase`. |
| `cycle_max_issues` | int | `10` | Safety cap on `/iflow-cycle` queue length (raise per run with `max:<n>`). |
| `cycle_onfail` | text | `"stop"` | Default `/iflow-cycle` failure policy: `stop` (halt) or `skip` (park and continue). Per-run `onfail:stop\|skip` overrides. |
| `cycle_nonyolo` | text | `"merge"` | Merge policy for `yolo: no` issues run hands-off by `/iflow-cycle`, `/iflow-auto` and `/iflow-drive`: `merge` (land the PR like yolo), `pr-only` (open the PR and continue; the next issue stacks on the branch), or `stop` (halt at the first one — the old behaviour). Per-run `nonyolo:merge\|pr-only\|stop` overrides. Env: `ISSUEFLOW_CYCLE_NONYOLO`. |
| `auto_adversarial_loops` | int | `2` | `/iflow-auto` review-and-fix loops per stage before it stops to ask (override per run with `loops:<n>`). |
| `confirm_version_bump` | bool | `false` | Non-yolo close asks once about a version bump when none was requested. |
| `ruff_autofix` | bool | `true` | When the project uses ruff, run `ruff check --fix` + `ruff format` during build and close. |
| `auto_close` | bool | `false` | `/iflow-build` (and the end of `/iflow-fix`) chain into `/iflow-close` when the work is ready; close keeps its own confirms. |
| `auto_plan` | bool | `true` | `/iflow-pick` chains into `/iflow-plan` after the pick and branch; trailing `noplan` skips once. |
| `auto_build` | bool | `true` | `/iflow-plan` chains into `/iflow-build` when you accept the plan; trailing `nobuild` skips once. |
| `early_pr` | bool | `false` | `/iflow-build` opens a draft PR after the first push; trailing `early` / `pr` / `noearly` override per run. |
| `fix_auto_name` | bool | `false` | `/iflow-fix` invents the session name without asking (creating the issue and branch still asks). |
| `locked` | bool | `false` | `issue-flow update --all` skips this repo. Project only. See [Per-repo lock](#per-repo-lock). |
| `confirm_changelog_update` | bool | `false` | `/iflow-close` shows the changelog entry and asks once before writing; declining stops close. `false` writes without asking (`nohistory` still skips). |
| `defer_changelog` | bool | `false` | Issue branches never write the changelog; the entry goes in the status file and PR body and is applied on the default branch after merge (`issue-flow agent apply-changelog`). |
| `essential_tests` | bool | `false` | Opt-in essential-test suite: close runs `pytest -m essential` as its required local check and triages the tests an issue touched. |
| `test_runner` | text | `"pytest"` | Test runner for essential tests (only `pytest` for now). |
| `essential_marker` | text | `"essential"` | The pytest marker name for the essential suite. |
| `essential_review` | text | `"close"` | When to triage issue-touched tests: `close`, `build`, `both`, or `never`. |

## Modes

A **mode** selects which workflow surfaces (skills / slash commands) `init`
installs, so you can scaffold a lighter workflow when the full lifecycle is more
than you need. Three modes ship built in:

| Mode | What you get |
| --- | --- |
| `standard` (default) | The full workflow: planning, PRs, history, cleanup, graphify, and all helpers. |
| `novice` | Guided setup plus the straight-line lifecycle and the safety nets: `/iflow`, `/iflow-setup`, `/iflow-pick`, `/iflow-init`, `/iflow-capture`, `/iflow-issue`, `/iflow-plan`, `/iflow-build`, `/iflow-pause`, `/iflow-close`, `/iflow-cleanup`, `/iflow-status`, `/iflow-doctor`. No yolo / cycle / auto / epic / split / fix / review / archive / graphify. |
| `simple` | A markdown-only lifecycle (capture, plan, implement, park, status, archive). No PR/cleanup/yolo/fix/graphify automation. Includes `/iflow-archive` for condensing a large `03-solved-issues/` folder. |

```bash
issue-flow init --mode simple
```

### The `novice` preset

`--mode novice` is the only mode that also **seeds settings**, because a smaller
command list alone does not make the flow easier to follow. On a project that
does not have a `config.toml` yet, it writes one where every lifecycle step
stops and asks instead of chaining into the next:

| Setting | Novice | Standard default |
| --- | --- | --- |
| `auto_plan` | `false` | `true` |
| `auto_build` | `false` | `true` |
| `auto_close` | `false` | `false` |
| `label_flows` | `false` | `true` |
| `confirm_version_bump` | `true` | `false` |
| `confirm_changelog_update` | `true` | `false` |
| `suggest_graphify` | `false` | `true` |
| `noob` | `true` | `false` |
| `skill_level` | `basic` | `standard` |

Selecting `novice` implies `skill_level = "basic"`; passing `--skill-level`
explicitly on the same command line still wins.

A project that **already** has a `config.toml` keeps its settings — switching to
`novice` later changes the installed surfaces but never rewrites knobs you have
tuned. Adjust anything in the table by editing `config.toml` and re-running
`issue-flow update`.

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

Git hooks for automatic pull/push conversion are planned as a follow-up;
hooks remain opt-in.

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

## pstack skills

[pstack](https://github.com/cursor/plugins/tree/main/pstack) is Lauren Tan's
(poteto) MIT-licensed skills library for rigorous agent work. Cursor users can
install all of it with `/add-plugin pstack`; issue-flow additionally ships a
**curated subset** of its single-file skills so any project — on any supported
editor — can opt them in next to the `iflow-*` skills and have them refreshed
by `issue-flow update`.

The vendored skills (upstream names; bodies are verbatim, only an
`issue-flow-version` stamp and a provenance comment are added):

| Skill | Use it when |
| --- | --- |
| `unslop` | cutting AI tells from prose — PR bodies, `HISTORY.md` bullets, issue specs, docs |
| `tdd` | fixing a bug that has a cheap local test path: failing regression test first, then the fix |
| `blast-radius` | a small-looking diff might break something elsewhere; proves the one fact it is safe because of by running code |
| `technical-writing` | writing or reviewing docs, READMEs, RFCs, PR descriptions, commit messages |
| `bro` | restating the last message in plain human language |
| `principle-prove-it-works` | verifying against the real artifact before declaring done |
| `principle-subtract-before-you-add` | removing or simplifying before adding |
| `principle-fix-root-causes` | fixing the cause, not the symptom |
| `principle-test-behavior-not-implementation` | keeping tests on observable behaviour |

They are **off by default** and never part of a mode's `skills = "all"`. Opt in
with `pstack_skills` under `[issueflow]` — a list of upstream names or `"all"` —
then re-run `issue-flow update` (task path: [Use pstack skills](how-to/pstack-skills.md)):

```toml
[issueflow]
pstack_skills = ["unslop", "tdd", "blast-radius"]
```

Each selected skill lands at `<agent_dir>/skills/<name>/SKILL.md` (so `/unslop`
works exactly as in pstack's own docs), the managed rule body gains a short
"pstack skills" section listing what is installed, and `/iflow-close` /
`/iflow-build` gain soft, membership-gated suggestions (unslop the PR body,
blast-radius before the PR, tdd for bug-shaped issues). Nothing is ever run
automatically. Removing a name and re-running `update` prunes that folder.
Custom modes can also `add = ["pstack_tdd"]` (stem form: `pstack_` + name with
hyphens as underscores).

Skills that depend on Cursor multi-model subagents, bundled scripts, MCP
fan-out, or pstack's own lifecycle (`poteto-mode`, `interrogate`, `arena`,
`swarm`, `why`, …) are deliberately not vendored — install the full plugin for
those. If both are installed, the same-named skills simply coexist. Upstream
licence text ships as `_pstack_LICENSE.txt` next to the templates.

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
ops_label = "ops"     # no-PR / ops close (default: "ops"; wins over yolo)
publish_label = "publish"  # bump + GitHub release after merge (default: "publish")
```

Set `label_flows = false` to opt out, or change `yolo_label` / `ops_label` /
`publish_label` to use different trigger labels; re-run `issue-flow update`
after changing so the commands re-render. Yolo/ops routing is only honored when
the matching commands are part of the active mode.

**Publish-on-success** (`publish_label`) does not change which
skill `/iflow-pick` runs. On `/iflow-close`, a matching label is treated as a
bump request (bare label → patch; `publish:minor` or `publish:0.6.0` for
overrides). Illogical explicit versions stop and ask. After the PR merges,
yolo close or `/iflow-cleanup` creates `gh release create "v<version>"
--generate-notes`. Ops wins over publish (no PR → no release). Fast path:
`issue-flow agent publish-intent --issue <N> --json`.

Related off-path flows (see [Command reference](issue-workflow.md)):

- `/iflow-review` — propose which open issues should get the configured
  `yolo_label` (re-score all open issues; apply behind one confirm).
- `/iflow-cycle yolo` — alias for `label:<yolo_label>`; batch-process every
  open issue that carries that label under one up-front confirm.

## Per-repo lock

`[issueflow] locked = true` lives on the **project**
`.issueflows/config.toml` only (default `false`; missing key = unlocked).
It is a bulk-update skip, not a write-protect: `issue-flow update --all`
will list and skip locked roots; a single-repo
`issue-flow update <root>` still runs.

```bash
issue-flow config set locked true
issue-flow config show locked
```

`config set --global locked …` is refused. A `locked` key in the
user-global file is ignored. `ISSUEFLOW_LOCKED=true|false` wins for that
process only (CI / one-off include-or-skip without editing the file).

Design notes: [user-global-config.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/user-global-config.md).

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

## How settings are resolved

issue-flow reads settings from these layers (later beats earlier only
when a key is **unset** above it):

- **baked default**
- **`ISSUEFLOW_*` env / `.env`** (project root, via python-dotenv)
- **user-global** `config.toml` — Linux/macOS/WSL:
  `$XDG_CONFIG_HOME/issue-flow/config.toml` or `~/.config/issue-flow/config.toml`;
  native Windows: `%APPDATA%\issue-flow\config.toml`.
  WSL is the Linux view (no `/mnt/c/Users/…` or `%APPDATA%` reads).
  A native Windows install is a separate machine.
- **project** `.issueflows/config.toml` — wins over every layer below

So: **project `config.toml` > user-global > env > default**. A committed
project file stays portable; user-global fills knobs the project did not
set. `mode` and `locked` are project-only (`config set --global mode …`
or `locked` is refused). The one exception to "project beats env" is
`ISSUEFLOW_LOCKED`, which overrides the project file for a single run.
`issue-flow register` / `init` write `registry.toml` beside the
user-global file; `update --all` walks it.

```bash
issue-flow config show --global
issue-flow config set --global caveman_default true
```

Design notes: [user-global-config.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/user-global-config.md).

`init` / `update` also copy the `both` skills (`iflow-init`,
`caveman`, `grill-me`, `gh-ci`) into **every** editor user-global
skill dir (Cursor `~/.cursor/skills/`, Claude `~/.claude/skills/`,
Codex `~/.agents/skills/`, opencode `~/.config/opencode/skills/`),
even when `--editor` is Cursor-only. The project copy stays; a
project skill with the same name wins. `--editor` still controls
which project tree is written. Stamps for those global dirs live beside the
user-global config (`skill-stamps.json`), not in the repo. `--force`
overwrites a foreign global skill dir the same way it does a project
one. Design notes: [global-vs-local-skills.md](https://github.com/jepegit/issue-flow/blob/main/.issueflows/04-designs-and-guides/global-vs-local-skills.md).

### Environment-only variables

These are read from the environment or the project `.env` only; putting them
in `config.toml` has no effect.

| Variable                 | Default        | Description |
| ------------------------ | -------------- | ----------- |
| `ISSUEFLOW_DIR`          | `.issueflows`  | Name of the issue-tracking directory. |
| `ISSUEFLOW_EDITOR`       | `cursor`       | Default editor profile when `--editor` is not passed (`cursor`, `claude`, `opencode`, `codex`). |
| `ISSUEFLOW_AGENT_DIR`    | *(per editor)* | Override the agent/IDE config directory. When unset it is derived from the editor profile (e.g. `.cursor`, `.claude`, `.opencode`, `.codex`). |
| `ISSUEFLOW_DOCS_DIR`     | `docs`         | Where to write the workflow documentation file. |
| `ISSUEFLOW_HISTORY_FILE` | `HISTORY.md`   | Changelog file that `/iflow-close` updates (set to e.g. `CHANGELOG.md` for different conventions). |

`issue-flow init` **creates a starter `.env` when one is missing** (all
`ISSUEFLOW_*` lines written commented-out, so nothing is overridden until you
uncomment). It never replaces an existing `.env` — not even with `--force`; on
later runs it only *appends* commented hints for any `ISSUEFLOW_*` keys you
don't already have. `issue-flow update` does not touch `.env` at all.

`--mode` and `--skill-level` on the command line beat everything for that
run: `--mode` (CLI) > `config.toml` > `ISSUEFLOW_MODE` > `standard`.

The optional [graphify integration](graphify.md) additionally reads an LLM API
key (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`MOONSHOT_API_KEY`) from `.env` for its semantic `extract` pass.

### Creating `config.toml`

`init --mode <id>` is the usual way `.issueflows/config.toml` first appears, but
you can also materialize a fully-commented file on demand:

```bash
issue-flow config add            # create .issueflows/config.toml if missing
issue-flow config add --force    # regenerate its [issueflow] keys in place
```

It writes every key in [All settings](#all-settings), taking each value from
its `ISSUEFLOW_*` env var / `.env` when set, otherwise the issue-flow default.
An existing file is left untouched unless `--force` is passed, in which case the
keys are upserted while your comments and `[modes.*]` tables are preserved.
After changing any of these keys, re-run `issue-flow update` so the rule and
commands re-render (and so optional side effects like the Linguist
`.gitattributes` block can apply). Pass `--json` for a machine-readable result.
