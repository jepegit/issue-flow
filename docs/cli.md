# CLI reference

```
issue-flow init [PROJECT_DIR] [--force] [--skip-dep-check] [--editor EDITOR] [--mode MODE] [--skill-level LEVEL]
issue-flow update [PROJECT_DIR] [--skip-dep-check] [--editor EDITOR]
issue-flow graphify [-C PROJECT_DIR] [...graphify subcommand + args]
issue-flow status [PROJECT_DIR] [--local] [--json]
issue-flow agent state [PROJECT_DIR] [--json]
issue-flow agent preflight [PROJECT_DIR] [--json]
issue-flow agent switchback [PROJECT_DIR] [--json]
issue-flow agent version-plan [PROJECT_DIR] [--bump LEVEL ...] [--json]
issue-flow agent epic-status N [-C PROJECT_DIR] [--local] [--json]
issue-flow agent queue [N ...] [--label L] [--epic N] [-C PROJECT_DIR] [--json]
issue-flow agent resolve [-C PROJECT_DIR] [--from-file FILE] [--json]
issue-flow agent sweep [PROJECT_DIR] [--except N] [--dry-run] [--json]
issue-flow agent archive N [N ...] [-C PROJECT_DIR] [--dry-run] [--json]
issue-flow agent capture N [-C PROJECT_DIR] [--repo OWNER/REPO] [--force] [--json]
issue-flow config add [-C PROJECT_DIR] [--force] [--json]
issue-flow workspace init [WORKSPACE_DIR] [--default MEMBER] [--force] [--json]
```

## When to use which

| Goal | Command |
| --- | --- |
| First-time setup, or add missing files only | `issue-flow init` |
| Pull newer templates after `uv tool upgrade issue-flow` (or similar) | `issue-flow update` |
| Replace generated scaffolds without upgrading logic | `issue-flow init --force` |
| Rebuild the graphify knowledge graph | `issue-flow graphify` |
| See where every issue stands (focus / parked / solved / GitHub) | `issue-flow status` |
| Let an agent resolve lifecycle state / sweep / capture deterministically | `issue-flow agent ...` |
| Condense old solved issues into a dated summary (recoverable via git) | `/iflow-archive` (summary is agent-written; `issue-flow agent archive …` for the delete step) |

## `issue-flow init`

| Argument / Option  | Description |
| ------------------ | ----------- |
| `PROJECT_DIR`      | Project root directory. Defaults to `.` (current directory). |
| `--force`, `-f`    | Overwrite generated commands, rules, and workflow doc instead of skipping them. |
| `--skip-dep-check` | Skip the external-CLI dependency check (`git`, `gh`) and the confirmation prompt that follows if anything is missing. Useful in automation. |
| `--editor`, `-e`   | AI coding tool(s) to scaffold for: `cursor` (default), `claude`, `opencode`, `codex`, or `all`. Repeatable (`-e cursor -e claude`). See [Editor support](editors.md). |
| `--mode`, `-m`     | Scaffolding mode — which workflow surfaces to install: `standard` (default, full workflow) or `simple` (markdown-only lifecycle). Persisted to `.issueflows/config.toml`; `update` honours it. See [Modes](configuration.md#modes). |
| `--skill-level`    | Skill level — controls quality-tooling recommendations: `basic` (minimal), `standard` (default), `advanced` (opinionated type checking / linting / pre-commit guidance). Persisted to `.issueflows/config.toml`; `update` honours it. See [Skill levels](configuration.md#skill-levels). |

Running `init` again without `--force` is safe: generated scaffold files that
already exist are skipped, and **issue markdown under `.issueflows/` is never
touched** by `init` or `update`. The project brief at
`.issueflows/04-designs-and-guides/this-project.md` is also user-owned: `init`
creates it only when missing, even with `--force`. When the CLI detects an
existing scaffold, it reminds you about `update` and `--force`.

If a dependency is missing, `issue-flow init` prints the installation hints
and asks whether to continue anyway. You can bypass the prompt in automation
with `issue-flow init --skip-dep-check` (the same flag is available on
`issue-flow update`), and the prompt is also auto-skipped when stdin is not
a TTY (e.g. CI pipelines).

## `issue-flow update`

| Argument / Option  | Description |
| ------------------ | ----------- |
| `PROJECT_DIR`      | Project root directory. Defaults to `.` (current directory). |
| `--skip-dep-check` | Skip the external-CLI dependency check (`git`, `gh`) and the confirmation prompt that follows if anything is missing. |
| `--editor`, `-e`   | AI coding tool(s) to refresh for: `cursor` (default), `claude`, `opencode`, `codex`, or `all`. Repeatable. See [Editor support](editors.md). |

Use `update` after upgrading the **issue-flow** package to refresh the packaged
skills, command files where supported, rules file(s), and
`docs/issue-workflow.md` from the version you have installed. This
**overwrites** those generated files (unlike a plain second `init`) and prunes
retired generated command/skill files. It still does not modify arbitrary files
under `.issueflows/` (for example your `issue*_original.md` /
`issue*_status.md` files), and it creates any **new** `.issueflows/`
subdirectories required by the current package. If
`.issueflows/04-designs-and-guides/this-project.md` is missing, `update`
recreates the starter brief; if it exists, user content is preserved. `update`
also respects the project's persisted [mode](configuration.md#modes): it
refreshes only that mode's surfaces (and prunes any that the mode excludes). To
change mode, re-run `issue-flow init --mode <id>`.

## `issue-flow graphify`

Rebuilds the optional knowledge graph. See
[the graphify integration guide](graphify.md) for the full story (enabling,
API keys, subcommand pass-through).

## `issue-flow status`

A **read-only** overview of where every issue stands — the same picture the
`/iflow-status` skill produces, but computed deterministically in Python. It
reports the focus issue and its lifecycle stage, parked work, the solved-issue
count, and (unless `--local`) open GitHub issues cross-referenced against your
local `.issueflows/` folders.

| Argument / Option | Description |
| ----------------- | ----------- |
| `PROJECT_DIR`     | Project root directory. Defaults to `.` (current directory). |
| `--local`         | Skip the GitHub query; report only the local `.issueflows/` state. |
| `--json`          | Emit a machine-readable JSON object instead of the human-readable text report. |

A missing or unauthenticated `gh` never fails the command — the GitHub section
is simply skipped and noted.

## `issue-flow agent ...`

The `agent` sub-app exposes the deterministic, mechanical building blocks the
scaffolded skills repeat over and over, so an AI agent can ask the tool for an
answer (ideally with `--json`) instead of re-deriving lifecycle state by hand.
The scaffolded skills/commands use these as an **optional fast path** and fall
back to their manual steps when the CLI is not installed, so nothing breaks if a
project never installs `issue-flow`.

| Command | What it does |
| --- | --- |
| `agent state` | Resolve the focus issue (branch-derived number wins, else the single current group), its lifecycle stage (`init`/`plan`/`start`/`close`), and the suggested next command. |
| `agent preflight` | Branch hygiene report: default branch, clean/dirty working tree, ahead/behind vs `origin/<default>`, and a stale-branch flag when the issue is already archived. Runs `git fetch --prune` first. |
| `agent switchback` | The mechanical "switch back when safe" half of `/iflow-close`: refuses (exit 1) while the working tree is dirty — listing the paths — else runs `git switch <default>` and `git pull --ff-only`. A refused fast-forward is reported, never forced. Never deletes branches (that stays in `/iflow-cleanup`). |
| `agent version-plan` | **Read-only** next-version planning for the `iflow-version-bump` skill: detects the release strategy from `pyproject.toml` (static `[project] version` → uv; `dynamic = ["version"]` + setuptools-scm/hatch-vcs/versioningit → git tag), reads the current version (static field or latest tag), applies the PEP 440 bump arithmetic (`--bump` repeatable; omitted → the pre-release-aware default), and prints the exact commands. Never edits files or creates tags; a filled `this-project.md` release section is flagged (`brief_release_section`) and wins over detection. |
| `agent epic-status` | **Read-only** progress for a staged epic: parses `.issueflows/05-epics/epic<N>_plan.md` (the structure `/iflow-epic` writes) and cross-references published issue states via `gh` — stages with per-issue state and blockers, the current stage, and the next open, unblocked candidates. `--local` skips the GitHub lookups. Exit 1 when no plan file exists. |
| `agent queue` | **Read-only** execution-queue planner for the cycling workflow. Exactly one source — explicit issue numbers, `--label L`, or `--epic N` (the epic's current stage). Parses `Depends on #N` / `Blocked by #N` lines, topologically orders the queue, and reports `blocked` (open deps outside the queue), `skipped_closed`, and `independent` (no dependency relation to any other member — parallel-safe). A dependency cycle aborts with exit 1, naming the members; the explicit-numbers source refuses a partial fetch so a typo never shrinks the queue silently. |
| `agent resolve` | Resolve project root, owner/repo, branch, and sibling scaffolds — for [multi-root workspaces](editors.md#multi-root-workspaces). When no scaffold is found walking up, falls back to the **default member** from a workspace-root `issueflow-workspace.toml` (reported as `resolved_via_workspace_default: true`); explicit hints and the nearest scaffold always win. |
| `agent sweep` | Archive `issue<N>_*` groups out of `01-current-issues/` to `03-solved-issues/` (Done) or `02-partly-solved-issues/` (not Done). Use `--except N` to keep the focus issue and `--dry-run` to preview. |
| `agent archive` | Mechanical deletion half of `/iflow-archive`: remove the chosen groups' files from `03-solved-issues/` and report the pre-archive HEAD sha (for the recovery ref in the summary file). Summarising into `YYYY-MM-DD_archived_issues.md` stays agent-side. Refuses when a requested issue has no solved group. `--dry-run` to preview. |
| `agent capture N` | Fetch GitHub issue `N` with `gh` and write `issue<N>_original.md` (the `## Original issue text` body). Prints the comments payload so the agent can triage them; comment triage stays agent-side. Use `--repo`, `--force`, `-C`. |

All `agent` commands accept `--json` and degrade gracefully: read-only commands
never hard-fail when `git`/`gh` is missing (they return partial data with a
note), while `agent capture` needs `gh` and exits non-zero with a hint when it
is unavailable or the fetch fails. `agent archive` needs a clean working tree
and refuses when any requested issue has no files under `03-solved-issues/`.
`agent switchback` likewise refuses on a dirty tree and exits non-zero when any
git step fails, so an agent can safely treat exit 0 as "on an up-to-date
default branch".

## `issue-flow config add`

Creates `.issueflows/config.toml`, seeded from `.env` (or issue-flow defaults).
See [Creating config.toml](configuration.md#creating-configtoml).

## `issue-flow workspace init`

Creates `issueflow-workspace.toml` at the **workspace root** — the folder that
contains several scaffolded member repos — so lifecycle commands invoked from
outside any single repo (typically the workspace root) can fall back to a
declared **default ("parent") member** instead of stopping to ask.

| Argument / Option | Description |
| ----------------- | ----------- |
| `WORKSPACE_DIR`   | Workspace root directory. Defaults to `.` (current directory). |
| `--default`       | Member folder name lifecycle commands default to. Must be a scaffolded member; with exactly one member it is chosen automatically. |
| `--force`, `-f`   | Overwrite an existing registry file. |
| `--json`          | Emit a machine-readable JSON object. |

Members are auto-discovered (immediate child directories carrying an
`.issueflows/` tree); the command refuses when there are none, and when
`--default` names something that is not a scaffolded member — a typo must
never redirect git operations. The registry only ever fills the bottom of the
resolution order: explicit `root:`/`repo:` hints, the nearest scaffold, and
the issue-branch heuristic all still win. See
[multi-root workspaces](editors.md#multi-root-workspaces).
