# Scaffolding and editors

What `init` / `update` write, for which editors, and how the CLI helps agents. Each section below was a separate design note; they are grouped here so the folder stays small (issue #406).

<a id="editor-profiles"></a>

## Editor profiles (multi-tool scaffolding)

Context: issue #62 — make issue-flow able to scaffold for AI coding tools beyond
Cursor (Claude Code, opencode, Codex CLI).

### Decision

A single template tree is shared across editors; per-tool differences live in an
`EditorProfile` (`src/issue_flow/editors.py`). The `EDITORS` registry maps an
editor id to its `agent_dir`, `commands_dir` (or `None`), an optional
`rules_extra` `(template, output)`, and a `graphify_installer` (or `None`).
`build_manifest(profile)` (`templating.py`) turns a profile into the list of
templates to render; `run_init` / `run_update` loop once per selected profile.

Surfaces, by portability:

- **Skills** (`<agent_dir>/skills/<name>/SKILL.md`) — the portable core, emitted
  for every editor.
- **`AGENTS.md`** — the convergent rules target, emitted for every editor.
- **Slash commands** — only when the profile defines `commands_dir` (Codex has
  none; opencode uses singular `command/`).
- **Per-editor rules extra** — `.cursor/rules/issueflow-rules.mdc` (Cursor) and
  `CLAUDE.md` (Claude), layered on top of `AGENTS.md`.

### Key choices / alternatives

- **AGENTS.md as a managed block, not a manifest overwrite.** `AGENTS.md` is
  frequently hand-maintained, so `_ensure_agents_md` (`init.py`) only owns the
  content between `<!-- BEGIN/END issue-flow ... -->` markers (mirrors the
  existing `_ensure_dotenv_file` pattern). Create / refresh-in-place / append;
  never clobbers user content. This is why it is *not* in `build_manifest`.
- **One rules body source of truth.** `templates/rules/_body.md.j2` is included
  by the `.mdc`, `CLAUDE.md.j2`, and `AGENTS.md.j2` templates so the three never
  drift. The body is intentionally editor-neutral (no `editor_name`) so the
  shared `AGENTS.md` content is identical across editors (no churn when several
  editors are selected).
- **Backward compatibility.** Default `editor=cursor`; `ISSUEFLOW_AGENT_DIR`
  still overrides `agent_dir` when set explicitly, otherwise it is derived from
  the profile. Historical note: issue #62 kept Cursor slash commands for
  compatibility, with only the rename `docs/cursor-issue-workflow.md` →
  `docs/issue-workflow.md` plus the new shared `AGENTS.md`.
- **Cursor skills-first (issue #79).** Cursor 2.4+ documents Agent Skills under
  `.cursor/skills/`, exposes them through the slash menu, and ships
  `/migrate-to-skills` for dynamic rules and slash commands. Cursor therefore
  now has `commands_dir=None`: issue-flow emits `.cursor/skills/`,
  `.cursor/rules/issueflow-rules.mdc`, `AGENTS.md`, and docs, but no
  `.cursor/commands/`. `update` prunes only known generated issue-flow command
  files and preserves unrelated user commands.
- **De-Cursoring.** Brand wording uses `{{ editor_name }}`; graphify
  registration text is gated on `{{ graphify_installer }}`. Tests assert no
  literal "Cursor" leaks into non-Cursor outputs.
- **Rejected:** separate per-editor template trees (too much duplication).

### Deferred

Deep per-editor command/skill divergence for Codex (slash-command-free phrasing
beyond the shared note) is intentionally out of scope; skills + `AGENTS.md` are
the portable contract.

<a id="multi-editor-conversion"></a>

## Multi-editor conversion

Context: issue #23 — teams where developers use different AI coding tools need
a shared git layout and local materialization of editor-specific surfaces.

### Decision

- **Canonical store in git:** `.issueflows/agent/skills/` (rendered `SKILL.md`
  snapshots) + `manifest.json` + existing `.issueflows/` issue tracking +
  `AGENTS.md` managed block.
- **Generated locally:** per-editor trees (`.cursor/`, `.claude/`, `.opencode/`,
  `.codex/`), optional `CLAUDE.md`, workflow doc under `docs/`.
- **CLI:** `issue-flow convert --to <editor|canonical>` with `--prune-other` and
  `--gitignore`. `issue-flow init --canonical` bootstraps the team workflow.
- **Standards:** Agent Skills (`SKILL.md`, agentskills.io) is the portable core;
  no universal format exists for rules/commands — issue-flow renders those per
  profile from the shared template tree ([editor-profiles.md](scaffolding-and-editors.md#editor-profiles)).

### Solo vs team

| Workflow | Init | Git commits |
| --- | --- | --- |
| Solo (default) | `issue-flow init` | `.cursor/` (or chosen editor) as today |
| Team | `issue-flow init --canonical` | `.issueflows/agent/` + `AGENTS.md`; editor dirs gitignored |

### Deferred

- Opt-in git hooks (`post-checkout` → local editor, `pre-push` → canonical) —
  phase 2 of #23; compose separately from #101 issue-file hooks.
- Windsurf `EditorProfile` (#17).

### Link

- Issue: [#23](https://github.com/jepegit/issue-flow/issues/23)

<a id="global-vs-local-skills"></a>

## Global vs local packaged skills

**Issue:** [#282](https://github.com/jepegit/issue-flow/issues/282) /
[#293](https://github.com/jepegit/issue-flow/issues/293) /
epic [#269](https://github.com/jepegit/issue-flow/issues/269)
**Status:** decided 2026-09-17 (Stage 1); `both` materialize shipped
[#293](https://github.com/jepegit/issue-flow/issues/293). Honour
[user-global-config.md](./user-global-config.md).

### Context

User-global config (#281) is the contract for knobs / lock / registry /
`update --all`. This doc answers the leftover product question: which
**packaged skill stems** may also land in the editor's user-global
skill dir, and which stay project-local. Local always wins when both
exist.

### Placement values

| Value | Meaning |
|-------|---------|
| `local` | Write only under `<repo>/<agent_dir>/skills/<output>/`. |
| `global` | Write only under the editor's user-global skill dir. |
| `both` | Write the user-global copy **and** keep the project copy. Project dir with the same output name beats the user-global copy. |

No stem is `global`-only in v1: a fresh clone must still work without
a prior `update --all` or home-dir install.

### Editor user-global paths (verified 2026-09-17)

| Editor | User-global write target | Also reads (compat) | Notes |
|--------|--------------------------|---------------------|-------|
| Cursor | `~/.cursor/skills/<output>/` | Project `.cursor/skills/`, `.agents/skills/`; compat `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, `~/.codex/skills/`; user `~/.agents/skills/` | Official docs: [Cursor Agent Skills](https://cursor.com/docs/skills). **Cloud Agents sync only `~/.cursor/skills/`** — do not install Cursor globals into `~/.claude/skills/` as the primary path. |
| Claude Code | `~/.claude/skills/<output>/` | Project `.claude/skills/` | Comment hypothesis on #269 (`Cursor reads ~/.claude/skills/`) is **true for Cursor compat**, but Claude's own global dir is still `~/.claude/skills/`. |
| Codex | `~/.agents/skills/<output>/` | Legacy `~/.codex/skills/` still scanned | Current Codex docs prefer `~/.agents/skills`. Do not write the legacy path as primary. |
| opencode | `~/.config/opencode/skills/<output>/` | Compat `~/.claude/skills/`, `~/.agents/skills/` | Official docs: [OpenCode Agent Skills](https://opencode.ai/docs/skills/) (verified 2026-09-17). Primary write is XDG `~/.config/opencode/skills/`. Do not write opencode globals into `~/.claude/skills/` or `~/.agents/skills/` as the primary path. |

WSL uses the Linux home inside the distro (`~/.cursor/skills/`), not
the Windows `%USERPROFILE%` tree — same split as
[user-global-config.md](./user-global-config.md). Native Windows
opencode globals are `%APPDATA%\opencode\skills\`. No `/mnt/c` bridge
(#298).

**Local wins.** A project skill directory with the same output name
beats the user-global copy. Honour #276 stamps on **each** tree that
`update` writes: project stamps in
`.issueflows/agent/skill-stamps.json`; user-global stamps in
`$XDG_CONFIG_HOME/issue-flow/skill-stamps.json` (or
`~/.config/issue-flow/skill-stamps.json` / `%APPDATA%\issue-flow\skill-stamps.json`),
keys like `cursor/caveman`. `--force` is `overwrite_foreign` on both
trees.

### Stem table

Stems from `DEFAULT_SKILL_DIRS` + `PSTACK_SKILL_DIRS` in
`src/issue_flow/templating.py`. Output name is `skill_output_name`
(`iflow_iflow` → `iflow`; pstack keeps upstream names).

#### Lifecycle (`iflow_*`) — `local`, except `iflow_init`

Bound to this repo's mode, `.issueflows/` tree, and the issue-flow
version that last ran `update`. A machine-wide lifecycle copy would
skew across repos on different versions.

**Exception (#310):** `iflow_init` is `both`. The skill is the
chicken-egg entry point (you need it to run init; you need init to
get project skills). The user-global copy lets `iflow init` run in a
folder with no scaffold yet; the project copy still wins inside a
repo (version / mode accurate). First machine still needs one CLI
`init` / `update` or `uvx issue-flow workspace bootstrap` to plant
the global copy. Other `iflow_*` stems stay `local`.

| Stem | Output | Placement |
|------|--------|-----------|
| `iflow_iflow` | `iflow` | `local` |
| `iflow_setup` | `iflow-setup` | `local` |
| `iflow_pick` | `iflow-pick` | `local` |
| `iflow_init` | `iflow-init` | `both` |
| `iflow_capture` | `iflow-capture` | `local` |
| `iflow_comments` | `iflow-comments` | `local` |
| `iflow_plan` | `iflow-plan` | `local` |
| `iflow_build` | `iflow-build` | `local` |
| `iflow_pause` | `iflow-pause` | `local` |
| `iflow_close` | `iflow-close` | `local` |
| `iflow_cleanup` | `iflow-cleanup` | `local` |
| `iflow_pr_sync` | `iflow-pr-sync` | `local` |
| `iflow_yolo` | `iflow-yolo` | `local` |
| `iflow_ops` | `iflow-ops` | `local` |
| `iflow_fix` | `iflow-fix` | `local` |
| `iflow_issue` | `iflow-issue` | `local` |
| `iflow_split` | `iflow-split` | `local` |
| `iflow_status` | `iflow-status` | `local` |
| `iflow_workspace_git` | `iflow-workspace-git` | `local` |
| `iflow_doctor` | `iflow-doctor` | `local` |
| `iflow_review` | `iflow-review` | `local` |
| `iflow_archive` | `iflow-archive` | `local` |
| `iflow_epic` | `iflow-epic` | `local` |
| `iflow_cycle` | `iflow-cycle` | `local` |
| `iflow_auto` | `iflow-auto` | `local` |
| `iflow_drive` | `iflow-drive` | `local` |
| `iflow_version_bump` | `iflow-version-bump` | `local` |
| `iflow_history_update` | `iflow-history-update` | `local` |
| `iflow_graphify` | `iflow-graphify` | `local` |

#### Behaviour (standard surface, not a slash lifecycle) — `both`

User-style / cheatsheet skills are useful outside a single repo.
Keep the project copy so `standard` mode stays self-contained.

| Stem | Output | Placement |
|------|--------|-----------|
| `caveman` | `caveman` | `both` |
| `grill_me` | `grill-me` | `both` |
| `gh_ci` | `gh-ci` | `both` |

#### pstack (optional) — all `local`

Opt-in via `[issueflow].pstack_skills`. Not in mode `"all"`. See
[pstack-skills.md](./pstack-skills.md).

| Stem | Output | Placement |
|------|--------|-----------|
| `pstack_unslop` | `unslop` | `local` |
| `pstack_tdd` | `tdd` | `local` |
| `pstack_blast_radius` | `blast-radius` | `local` |
| `pstack_technical_writing` | `technical-writing` | `local` |
| `pstack_bro` | `bro` | `local` |
| `pstack_principle_prove_it_works` | `principle-prove-it-works` | `local` |
| `pstack_principle_subtract_before_you_add` | `principle-subtract-before-you-add` | `local` |
| `pstack_principle_fix_root_causes` | `principle-fix-root-causes` | `local` |
| `pstack_principle_test_behavior_not_implementation` | `principle-test-behavior-not-implementation` | `local` |

### Materialize (`init` / `update` / `update --all`)

`init` and `update` (including each `update --all` member) write the
`both` stems into **every** editor user-global path above, and keep
the project copy. `--editor` still selects only the **project** tree.
Stems omitted by the active mode (e.g. `simple`) are not written. No
`global`-only stems. Not a skillbook library
([skillbook-lessons.md](./skillbook-lessons.md)). A Cursor-only
`update` still plants `iflow-init` in `~/.agents/skills/` and
`~/.claude/skills/` so switching harness does not need a second
`--editor` pass (issue #339).

Do **not** collapse Cursor + Claude into one shared `~/.claude/skills/`
tree: Cursor Cloud sync is `~/.cursor/skills/` only.

### Later

- Any future `global`-only stems (none in v1). `iflow_init` is `both`,
  not `global`-only: a fresh clone still gets the project copy.

### Link

Epic plan: `.issueflows/05-epics/epic269_plan.md`.  
User-global knobs: [user-global-config.md](./user-global-config.md).  
Editor profiles: [editor-profiles.md](./editor-profiles.md).

<a id="user-global-config"></a>

## User-global config, lock, registry, and update-all

**Issue:** [#281](https://github.com/jepegit/issue-flow/issues/281) (this
contract) / epic [#269](https://github.com/jepegit/issue-flow/issues/269)
**Status:** decided 2026-09-17 (Stage 1). User-global file + resolve +
`config show|set --global` shipped in #285. Per-repo `locked` shipped
in #286. Registry + `update --all` shipped in #287.

### Context

A user wants **one machine-wide default** for issue-flow knobs, a
**registry** of repos that use issue-flow on this computer, a way to
**lock** some of those repos so bulk-update leaves them alone, and one
command that refreshes every unlocked registered stack. Workspace
update already covers sibling members of an
`issueflow-workspace.toml`. This layer sits **above** that: no
workspace file required, any registered root is eligible.

Not a skillbook clone. [skillbook-lessons.md](./skillbook-lessons.md)
already pointed #269 at user-global config + update-all + lock and
rejected a personal skill library. Which packaged stems may also
install user-global is decided in
[global-vs-local-skills.md](./global-vs-local-skills.md) (#282).

### Decisions

#### User-dir layout

| OS | Directory |
|----|-----------|
| Linux / macOS | `$XDG_CONFIG_HOME/issue-flow/` when `XDG_CONFIG_HOME` is set, else `~/.config/issue-flow/` |
| Windows (native) | `%APPDATA%\issue-flow\` (Roaming) |
| WSL | **Linux path inside the distro** (`~/.config/issue-flow/` or `XDG_CONFIG_HOME`). Do not read the Windows `%APPDATA%` tree from WSL Python (no `/mnt/c/Users/…` lookup). A native Windows install is a separate machine view. The `win32` branch is covered by tests that monkeypatch `sys.platform` (#298). |

Files in that directory:

| File | Role |
|------|------|
| `config.toml` | User-global `[issueflow]` **preference** knobs |
| `registry.toml` | Absolute project roots that `update --all` walks |

Create the directory and files on first write (`config set --global`,
`register`, or `init` registering the current root). Missing files mean
"no user-global layer" — today's resolve behaviour.

#### Precedence

For `[issueflow]` **preference knobs** (the keys already documented in
[skill-behaviour-knobs.md](./skill-behaviour-knobs.md)):

**project `.issueflows/config.toml` > user-global `config.toml` >
`ISSUEFLOW_*` env / `.env` > baked default**

Justification: this **extends** the existing contract
(`config.toml` > env > default) instead of reversing it. A committed
project file stays portable and CI-stable; user-global fills knobs the
project did not set; env remains the last explicit override before
code defaults. "System-wide defaults win over the project" was
rejected — that would make a laptop preference silently override a
repo that already chose otherwise.

**Not in user-global** (ignore the key if present):

- `mode` — project identity; only `init --mode` writes it.
- `locked` — per-repo skip flag (below).
- Path keys (`ISSUEFLOW_DIR`, `ISSUEFLOW_AGENT_DIR`,
  `ISSUEFLOW_DOCS_DIR`, `ISSUEFLOW_HISTORY_FILE`) — stay
  **environment-only**, as today.

CLI flags (`--mode`, `--editor`, `--force`, …) still beat every file.

#### Lock

`[issueflow] locked = true` lives on the **project**
`.issueflows/config.toml` only. Default is **false** (missing key =
unlocked).

- `update --all` **lists and skips** locked roots; it does not run
  `update` on them.
- A single-repo `issue-flow update <root>` does **not** refuse a locked
  repo — lock is a bulk-update skip, not a write-protect on the
  project itself.
- User-global `locked` is invalid and ignored.
- Optional process override: `ISSUEFLOW_LOCKED=true|false` wins for
  that invocation only (the one exception to project-beats-env). Use
  it in CI or a one-off shell to skip or force-include without
  editing `config.toml`.

#### Registry

`registry.toml` is a list of absolute roots:

```toml
roots = [
  "/home/you/src/issue-flow",
  "/home/you/src/other-app",
]
```

- **Both** `issue-flow init` (adds the current root when missing) and
  an explicit `issue-flow register [PROJECT_DIR]` write the registry.
  `issue-flow workspace bootstrap --yes` inits each git sibling via
  `init`, so those roots are registered the same way. No extra registry
  knob.
  `issue-flow unregister [PROJECT_DIR]` removes a root. Writes are
  idempotent.
- No whole-disk scan on `update --all` / `init` / `workspace update`.
  Missing roots are skipped and reported, not treated as a hard failure.
  Opt-in: `issue-flow register --discover [START]` walks a start
  directory for existing `.issueflows/` trees (bounded depth, no
  symlink follow) and registers only after confirm (`--yes` for
  scripts).
- Roots are stored resolved (absolute). Relative paths are rejected
  on write.
- `.issueflows/` tracking, epic plans, and project knobs stay
  **per-repo**. The registry is only a list of places to run `update`.

#### `update --all` vs `workspace update`

| Command | Set | Needs workspace file? |
|---------|-----|------------------------|
| `issue-flow update --all` | Registry roots | No |
| `issue-flow workspace update` | Scaffolded members of `issueflow-workspace.toml` | Yes |

Keep the name **`update --all`** (compose with the existing command;
no second verb). It walks the registry, skips missing and **locked**
roots, runs `update` on the rest, and aggregates ok / skip / fail the
same way `workspace update` does (one member failure does not abort
the rest).

Flags `--editor`, `--skip-dep-check`, and `--force` forward to each
member `update`. `--force` is the #276 `overwrite_foreign` switch.

A repo may appear in both the registry and a workspace file. Default
command sets stay different (`update --all` = registry;
`workspace update` = workspace members). `update --all --workspace`
unions the nearest workspace file's members with the registry, unique
by resolved path, so an overlapping root is refreshed once in that
invocation. `workspace update` also collapses a member listed twice.

#### #276 stamps on a registered repo

Each registered root keeps its own
`.issueflows/agent/skill-stamps.json`. `update --all` running `update`
on that root uses **that repo's** stamps: skip foreign packaged skill
dirs (symlink, extra files, hash ≠ last-write stamp) unless `--force`
was passed on the `--all` invocation.

User-global **skill** materialize (#293) writes a second stamp file at
`$XDG_CONFIG_HOME/issue-flow/skill-stamps.json` (or
`~/.config/issue-flow/skill-stamps.json` /
`%APPDATA%\issue-flow\skill-stamps.json`), keys
`{editor_id}/{output_name}` (e.g. `cursor/caveman`). `--force` on
`update` / `update --all` is `overwrite_foreign` for those global dirs
too. Honour [skillbook-lessons.md](./skillbook-lessons.md): no second
library. #277 unmanaged-skill scan stays a project-doctor concern
(global dirs are not scanned).

### Knobs

New project key (see [skill-behaviour-knobs.md](./skill-behaviour-knobs.md)):

| Key | Default | Effect |
|-----|---------|--------|
| `locked` | `false` | `update --all` skips this root. Project `config.toml` only. |

User-global path / registry path are **not** project knobs. They follow
the OS table above.

### Stage 2 must implement

Cite this doc from the Stage 2 issues:

1. User-global `config.toml` + resolve precedence +
   `config show|set --global`.
2. Persist `[issueflow] locked` (default false) + `ISSUEFLOW_LOCKED`.
3. Registry + `register` / `unregister` + `update --all`.

### Non-goals (this contract)

- Vendoring skillbook or a personal skill library.
- Default whole-disk scan (opt-in `register --discover` only, #297).
- GitLab.
- Making every packaged skill global (#282 / #293: only `both` stems).
- Deduping `update --all` with `workspace update` except the opt-in
  `--workspace` union (#296).
- Windows-native paths from inside WSL (explicit non-goal; #298 tests the
  `win32` branch only).

### Link

Epic plan: `.issueflows/05-epics/epic269_plan.md`.  
Knobs: [skill-behaviour-knobs.md](./skill-behaviour-knobs.md).  
Workspace registry: [multi-repo-workspaces.md](./multi-repo-workspaces.md).  
Clobber-protect: issue #276 / `skill_ownership.py`.

<a id="project-brief-scaffold"></a>

## Project brief scaffold

Context: issue #53 — add a generated project-summary document that agents and
humans can use for quick repo orientation.

### Decision

`this-project.md` lives at `.issueflows/04-designs-and-guides/this-project.md`
and is user-owned durable memory. `issue-flow init` and `issue-flow update`
create it from `src/issue_flow/templates/docs/this-project.md.j2` only when the
file is missing; they never overwrite existing content, including when
`init --force` is used.

The brief is deliberately not part of `build_manifest()`. Manifest outputs are
package-owned scaffold files and `run_update` refreshes them with `force=True`.
The project brief follows the special "ensure" pattern used for other
user-preserving outputs instead.

### Alternatives considered

- Put the brief in `build_manifest()` and rely on `init` skipping existing files:
  rejected because `run_update` overwrites manifest files.
- Manage a marker-delimited block inside the brief: rejected because the whole
  file should be freely hand-editable, not partly package-owned.
- Autofill from README / package metadata in v1: deferred; placeholders are
  predictable and avoid surprising generated claims.

<a id="linguist-gitattributes"></a>

## Linguist `.gitattributes` (issue #168)

### Context

GitHub Linguist language stats can be skewed by non-library trees (especially
`graphify-out/graph.html` as HTML). issue-flow offers an optional managed
`.gitattributes` block so consumers can keep stats focused on library source.

### Decision

- Config key: `[issueflow].linguist_attributes` (default **`false`**, opt-in).
- Env fallback: `ISSUEFLOW_LINGUIST_ATTRIBUTES`.
- When true, `issue-flow init` / `update` append a marker-delimited block to
  root `.gitattributes` (same idempotent pattern as the editor `.gitignore`
  block). Existing user rules outside the markers are left alone.
- When false: do not write; do **not** strip an existing managed block.
- Shared path set is fixed/generic (issue #168 example); no per-project path
  discovery in v1.

### Alternatives considered

- Dogfood-only committed file with no user option — rejected; users hit the
  same Linguist skew with graphify / docs / `.issueflows/`.
- Default on — rejected; writing root git metadata is surprising for existing
  projects.

<a id="python-toolchain-deference"></a>

## Python toolchain deference (don't hard-mandate uv)

Context: issue #58 — issue-flow scaffolds rules that hard-mandated `uv`
("Use `uv` exclusively, never pip/poetry"). When scaffolded into a project that
uses a different toolchain (notably **conda**), those rules fight the project's
real setup: conda projects need Python and `pytest` run inside the **activated
conda environment**, not via `uv run`.

### Decision

The scaffolded rules **defer to the project's existing, documented toolchain**.
`uv` remains the *default/example* (issue-flow itself is uv-managed, and it's the
assumption for freshly scaffolded projects), but it is framed as one option,
conditional on what the project documents.

- Source of truth: the "Running python" section of
  [`templates/rules/_body.md.j2`](../../src/issue_flow/templates/rules/_body.md.j2),
  which feeds `AGENTS.md`, `CLAUDE.md`, and the Cursor `.mdc` (one body, three
  outputs — see [editor-profiles.md](scaffolding-and-editors.md#editor-profiles)).
- Structure: a "respect existing tooling first" preamble + one tool-neutral
  principle (never bare `python ...`), then branches for **conda** (activate the
  env / `conda run -n <env>`), **uv** (the default), and **other** (venv/pip/
  poetry).
- The prescriptive `uv run` / `uv add …` phrasings in the `issue-start` and
  `issue-plan` command/skill templates were softened to "the project's documented
  toolchain (e.g. `uv run`, or inside the activated conda env)".

### Alternatives considered

- **`ISSUEFLOW_PYTHON_RUNNER` config toggle** (uv|conda|pip) driving rendered
  examples — rejected: more machinery than the issue warranted, and deference is
  a *runtime* concern (the agent reads the project's rules) rather than a
  scaffold-time switch. Wording-only keeps one editor-neutral body.
- **Genericising `uv version --bump`** in the version-bump templates — left
  as-is: it's genuinely uv-specific, gated behind an opt-in `bump` argument, and
  already skips when there's no bumpable `pyproject.toml`.

### Notes

- The body is intentionally editor-neutral (no `{{ editor_name }}`) so shared
  `AGENTS.md` content stays identical across editors.
- This repo dogfoods its own scaffold; after template edits, regenerate via
  `scripts/update_issueflow_setup.py` (≈ `issue-flow update .`) so the root
  `AGENTS.md` managed block and `.cursor/rules/issueflow-rules.mdc` match.

<a id="agentic-cli"></a>

## Agent-facing CLI commands

_Issue: #88. Status: implemented. Extended by #84 (`agent archive`)._

### Context

Until #88, the `issue-flow` package only scaffolded (`init`/`update`/`graphify`)
and **no Python read the `.issueflows/` tree** — every lifecycle mechanic
(state detection, folder sweeps, branch preflight, `gh` issue fetch) lived as
agent instructions in the Jinja templates and was re-derived by hand on each run.

### Decision

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
  Decode captured output as **UTF-8** with `errors="replace"` (issue #216):
  locale decoding (Windows `cp1252`) crashes on UTF-8 `gh issue view` bodies,
  and a failed reader can leave `stdout is None` — callers must not `.strip()`
  a `None` stream.

### Key constraints (honour these in future work)

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

### Alternatives considered

- **Grouping everything top-level** vs an `agent` namespace — chose hybrid:
  `status` is generally useful (top-level), the rest are agent-oriented and
  grouped under `agent`.
- **A git-hook/daemon to move issue files** — out of scope; `agent sweep` keeps
  it explicit and previewable (`--dry-run`).

### Follow-up: `agent archive` (#84)

`issue-flow agent archive <N> ...` follows the same pattern for
`/iflow-archive`: only the **mechanical half** (deleting solved
`issue<N>_*` files, reporting the pre-archive HEAD sha) is promoted;
the per-issue summarisation into the dated
`YYYY-MM-DD_archived_issues.md` file stays agent-side. It refuses the
whole run (exit 1, nothing deleted) when any requested issue has no
group in the solved folder, so a typo never archives less than the
user confirmed. Recovery contract: the summary file records the
pre-archive sha; originals come back via `git show <sha>:<path>`.

<a id="dirty-issueflows"></a>

## Dirty `.issueflows/` directories

_Issue: #47._

### What “dirty” means

A dirty tree has filesystem state that makes the issue-flow lifecycle
(`/iflow`, init/start sweeps, focus resolution) behave inconsistently or stall.
These conditions are **machine-checkable** — the same rules power
`issue-flow doctor`, `issue-flow agent audit`, and `/iflow-doctor`.

| Code | Condition | Severity | Auto-repair |
| --- | --- | --- | --- |
| `multi_focus` | More than one `issue<N>_*` group in `01-current-issues` while focus is ambiguous (no `N-slug` branch) | error | partial — pass `--except N` or switch branch |
| `leftover_in_current` | Issue group in `01` that is not the resolved focus | warn | yes — sweep to `02`/`03` |
| `duplicate_across_folders` | Same issue number in two of `01`/`02`/`03` | error | no — manual merge |
| `done_still_in_current` | Focus issue in `01` with `- [x] Done` | warn | no — run `/iflow-close` |
| `incomplete_group` | `issue<N>_plan` or status file without `issue<N>_original` in that folder | warn | no — run `/iflow-init` |
| `orphan_file` | Unexpected file in a lifecycle folder (allowlist: `cycle_status.md`) | info | no |
| `missing_tree_folder` | Expected `.issueflows/` subfolder absent | info | yes — `mkdir` |
| `unmanaged_editor_skill` | Directory under an in-use `<agent_dir>/skills/` whose name is not a packaged `SKILL_DIRS` output (`my-notes`, leftover retired names, …) | info | no — report only; `update` already leaves it alone |

### CLI

```bash
issue-flow doctor              # audit; exit 1 on error-level findings
issue-flow doctor --json
issue-flow doctor --fix        # mkdir + sweep non-focus groups
issue-flow doctor --fix --dry-run --except 47
issue-flow agent audit         # same as doctor (agent fast path)
issue-flow agent repair        # same as doctor --fix
```

Repairs never delete issue markdown — they only create missing folders and
move whole groups using the same rules as `issue-flow agent sweep`.

### Agent skill

`/iflow-doctor` (off-path) runs audit, presents findings, and on confirmation
applies `--fix`. Manual fallback steps live in the skill template when the CLI
is not installed.

### Post-repair git housekeeping (issue #218)

`doctor --fix` / `agent repair` stay **filesystem-only** — they never run
`git commit`. Repairs typically leave a dirty tree whose paths are all under
`.issueflows/` (moved `issue<N>_*` groups).

**Agent convention:**

1. After a successful `/iflow-doctor` repair, if
   `issue-flow agent preflight --json` reports `issueflows_only: true` (or every
   porcelain path is under the configured issueflows dir), treat **commit
   housekeeping** as the **recommended default** — one confirm, stage only
   those paths, message like
   `chore: doctor housekeeping — archive/sweep .issueflows groups`, **no push**.
2. `/iflow-pick` Phase 2 uses the same rule when the tree is dirty: issueflows-only
   → offer that default commit then continue; any path outside `.issueflows/` →
   hard stop (commit/stash/abort), never “commit everything”.
3. Never fold `src/` (or other non-issueflows paths) into the housekeeping
   commit.
