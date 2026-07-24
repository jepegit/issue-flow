# Agent-facing CLI commands

_Issue: #88. Status: implemented. Extended by #84 (`agent archive`)._

## Context

Until #88, the `issue-flow` package only scaffolded (`init`/`update`/`graphify`)
and **no Python read the `.issueflows/` tree** — every lifecycle mechanic
(state detection, folder sweeps, branch preflight, `gh` issue fetch) lived as
agent instructions in the Jinja templates and was re-derived by hand on each run.

## Decision

Promote the deterministic, non-LLM mechanics into real subcommands:

- Top-level `issue-flow status [--local] [--json]` — human-facing overview.
- An `agent` Typer sub-app for agent-driven mechanics: `agent state`,
  `agent preflight`, `agent sweep`, `agent capture` (all support `--json`).

Two new core modules back them:

- `tracking.py` — pure-filesystem reader of `.issueflows/` (issue grouping, the
  `- [x] Done` rule, lifecycle stage, focus resolution, sweep plan/apply). The
  single source of truth in code for conventions previously only in templates.
- `gitutils.py` — best-effort `git`/`gh` wrappers following the `graphify.py`
  pattern (`shutil.which` -> argv list -> `subprocess.run(check=False)`),
  returning `None` when a tool is absent. **Never `shell=True`.**

## Key constraints (honour these in future work)

- **Uniform `-C` / `--project-dir` on every `agent` subcommand** (issue #211).
  Skills tell agents to pass `-C <project_root>` after `agent resolve`; do not
  reintroduce a positional project-dir Argument on new `agent` commands.
  Top-level `status` / `doctor` / `init` / `update` may stay positional.
- **CLI is optional, never assumed.** A scaffolded repo only has `issue-flow`
  if the user installed it. Skills/commands therefore use the CLI as a *fast
  path* and keep their manual steps as a fallback — mirror this for any new
  promoted command. Do not make a skill hard-depend on the CLI.
- **Read-only commands degrade gracefully.** Missing/unauthenticated `gh` (and
  missing `git`) must yield partial data + a note, not an error. Only
  `agent capture` (which needs `gh`) exits non-zero when it cannot fetch.
- **LLM judgment stays agent-side.** Comment triage, GitHub issue ranking, and
  planning are intentionally NOT promoted — only mechanical steps are.
- **Untrusted content is data, not instructions.** `agent capture` writes the
  GitHub issue body/title/comments verbatim (a prompt-injection channel for
  downstream agents) and prints comments for triage; it never executes them.
  Text output `rich.markup.escape()`s untrusted titles/branch names; the
  `--json` path is the safe interface for agents to consume.

## Alternatives considered

- **Grouping everything top-level** vs an `agent` namespace — chose hybrid:
  `status` is generally useful (top-level), the rest are agent-oriented and
  grouped under `agent`.
- **A git-hook/daemon to move issue files** — out of scope; `agent sweep` keeps
  it explicit and previewable (`--dry-run`).

## Follow-up: `agent archive` (#84)

`issue-flow agent archive <N> ...` follows the same pattern for
`/iflow-archive`: only the **mechanical half** (deleting solved
`issue<N>_*` files, reporting the pre-archive HEAD sha) is promoted;
the per-issue summarisation into the dated
`YYYY-MM-DD_archived_issues.md` file stays agent-side. It refuses the
whole run (exit 1, nothing deleted) when any requested issue has no
group in the solved folder, so a typo never archives less than the
user confirmed. Recovery contract: the summary file records the
pre-archive sha; originals come back via `git show <sha>:<path>`.
