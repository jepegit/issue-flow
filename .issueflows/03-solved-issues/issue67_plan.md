# Issue #67 — Plan

## Goal

Make issue-flow usable in **multi-root Cursor workspaces** (sibling repos scaffolded independently) by eliminating silent wrong-repo operations and reducing merged-rule conflicts. Deliver **Phase 1** in this issue; defer workspace registry, cross-repo linking, and multi-repo status to follow-ups.

## Constraints

- **Templates are source of truth** — behaviour changes land in `src/issue_flow/templates/`, not rendered copies under `.cursor/`.
- **Back-compat** — single-repo workflows must keep working unchanged; new resolution steps are additive (explicit hints + deterministic fallbacks, then ask).
- **No silent cross-repo side effects** — every `git`/`gh` call in lifecycle skills must target a **resolved project root** and **explicit `owner/repo`**.
- **Scope limit for #67** — Phase 1 only (see Approach). Do not block on #12 (in-repo linked issues) or a full #20-style multi-repo dashboard.
- **Python 3.13+, `uv` only** for new CLI code; match existing `gitutils` / `agent` patterns.

### Prior art

- [`gitutils.py`](../../src/issue_flow/gitutils.py) — thin `git`/`gh` wrappers; already accept `cwd: Path` and optional `--repo`; used by `agent capture`, `preflight`, `status`. **Extend**, don't duplicate.
- [`agent.py`](../../src/issue_flow/agent.py) — `run_capture` resolves `owner/repo` from origin when `--repo` omitted; `run_preflight` / `run_status` assume caller passes correct `project_dir` via `-C`. **Add a `resolve` subcommand** so agents don't re-derive this by hand.
- [`cli.py`](../../src/issue_flow/cli.py) — agent subcommands already support `--project-dir` / `-C` on `capture`, `preflight`, `sweep`, `archive`. **Mirror on new `resolve` and document in templates.**
- [`tracking.py`](../../src/issue_flow/tracking.py) — `resolve_focus()` for `/iflow` dispatch; branch-derived `N` wins. Unchanged; root resolution is orthogonal.
- [`issueflow-rules.mdc.j2`](../../src/issue_flow/templates/rules/issueflow-rules.mdc.j2) — today `alwaysApply: true` with empty `globs:` → rules from every scaffolded repo merge in multi-root workspaces. **Coexist → fix via scoped globs.**
- [`editor-profiles.md`](../../.issueflows/04-designs-and-guides/editor-profiles.md) — one shared `_body.md.j2`; per-editor rules extra is the right place to scope Cursor rules.
- [`verify_scaffold.py`](../../.issueflows/00-tools/verify_scaffold.py) — reuse for end-to-end template smoke after rule/scaffold changes.
- **Comment on #67** — `/iflow-pick <n> repo:<repo-name>` may work ad hoc via LLM; plan replaces luck with deterministic resolution, keeping `repo:` / `root:` hints as first-class input syntax.
- **Graph (Community around `gitutils`, god-node “branch and folder hygiene”)** — confirms lifecycle templates and rules body are the touch surface, not init scaffolding alone.

## Approach

### Why phased

The issue lists five independent friction points and five optional improvements. Shipping everything in one PR mixes CLI, template, Cursor rule semantics, workspace config, and cross-repo issue tooling. **Phase 1** fixes the dangerous silent-misroute class (points 1, 2, 5) and the worst rule-collision class (point 3) without new persistent workspace config.

| Phase | Delivers | Issue points | Defer to |
| --- | --- | --- | --- |
| **1 (this PR)** | Root/repo resolution contract + CLI helper + template/skill updates + scoped Cursor rules + design doc | 1, 2, 3 (partial), 5 (partial) | — |
| **2** | `workspace.toml` registry, multi-root `/iflow-pick` ranking | workspace mode, pick across repos | new issue |
| **3** | Cross-repo linked issues, paired-issue helper | 4 | #12 + new issue |
| **4** | Multi-repo `issue-flow status` dashboard | multi-repo status | #20 extension |

### Phase 1 — design

#### 1. Deterministic project-root discovery (Python)

Add `issue_flow/project.py` (name TBD) with:

```python
def find_project_root(start: Path, *, issueflows_dir: str = ".issueflows") -> Path | None
```

Walk parents from `start` (or `Path.cwd()`) until `/<issueflows_dir>/config.toml` or `/<issueflows_dir>/01-current-issues/` exists; return that directory. Used by CLI and documented for agents as the canonical algorithm.

Add `issue_flow/agent.py::run_resolve()` + CLI:

```bash
issue-flow agent resolve [-C <dir>] [--from-file <path>] [--json]
```

JSON payload (stable keys):

```json
{
  "project_root": "/abs/path/to/cellpy-core",
  "repo": "owner/cellpy-core",
  "branch": "13-migrate-foo",
  "default_branch": "main",
  "issueflows_dir": ".issueflows"
}
```

- `-C` sets the search start (default `.`).
- `--from-file` starts the walk from a file path (simulates “active editor file” for agents/tests).
- `repo` always populated when `origin` parses; never rely on `gh`’s implicit cwd default in templates again.

#### 2. Resolution contract in lifecycle templates

Introduce shared Jinja partial `templates/skills/_resolve_project_root.md.j2` included at the top of lifecycle skills/commands that touch git/gh or `.issueflows/`:

**Resolution order** (stop when unambiguous):

1. **Explicit user hint** in slash input — `root:<path>`, `repo:<folder-name>`, or `repo:owner/name` (document grammar; `repo:cellpy-core` matches a registered workspace folder name in Phase 2; in Phase 1 match **directory basename** under the Cursor workspace when the agent can see multiple roots, else match `owner/repo`).
2. **CLI fast path** — `issue-flow agent resolve [--from-file <active-file>]` (prefer over hand-rolled logic).
3. **Branch context** — if cwd/branch search finds exactly one repo whose branch matches `^\d+-`, prefer that root (common case: already on issue branch in one repo).
4. **Single candidate** — exactly one `.issueflows/` tree visible in the workspace → use it.
5. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, **mandate**:

- Shell git: `git -C <project_root> …` (or exclusively `issue-flow agent … -C <project_root>` for supported ops).
- Shell gh: always `--repo <owner/name>` from resolved root (never bare `gh issue …`).
- File paths: all `.issueflows/…` paths relative to `<project_root>`.

**Skills/commands to update** (include partial + audit git/gh steps):

- `iflow_init`, `iflow_close`, `iflow_cleanup`, `iflow_pick`, `iflow_status`, `iflow`, `iflow_start` (preflight), `iflow_plan` (preflight), `iflow_pause`, `iflow_yolo`, `iflow_fix`
- Matching `commands/*.md.j2` where they still exist / differ from skills
- `rules/_body.md.j2` — short **Multi-root workspaces** subsection pointing at the design doc and the resolution contract

#### 3. Scope always-on Cursor rules (point 3)

Update [`issueflow-rules.mdc.j2`](../../src/issue_flow/templates/rules/issueflow-rules.mdc.j2):

```yaml
---
description: Issue-flow workflow rules for {{ project_name }}
globs:
  - "**/*"
alwaysApply: false
---
```

Rationale: in multi-root workspaces, Cursor attaches each repo's `.cursor/rules/` to **that** root; `alwaysApply: true` merges globally. Scoped globs keep each repo's issue-flow rules active only when working under that root.

**AGENTS.md** managed block stays `alwaysApply`-equivalent (editors merge it) — document in the design doc that per-repo toolchain rules belong in `this-project.md` / scoped `.mdc`, not duplicated conda vs uv instructions in the shared `_body.md.j2`. Optional: add one line to the scaffolded `this-project.md.j2` reminding authors to put toolchain-specific run/test commands there.

`issue-flow update` on existing projects refreshes the `.mdc` front matter (manifest output).

#### 4. Design doc + README section

Add [`.issueflows/04-designs-and-guides/multi-repo-workspaces.md`](../../.issueflows/04-designs-and-guides/multi-repo-workspaces.md) (source: new template or hand-authored in this repo):

- Recommended Cursor layout (sibling folders, one `issue-flow init` per repo).
- Resolution contract + hint syntax.
- What Phase 1 does / does not do.
- Manual cross-repo workflow until Phase 3 (paired issues, shared label — mirrors issue body).
- Link back to #67.

Add a short **Multi-root workspaces** subsection to README (or `docs/issue-workflow.md.j2`).

#### 5. `/iflow-cleanup` in multi-root

Extend cleanup skill: after completing one repo, **report** sibling scaffolded repos detected in the workspace (directories with `.issueflows/` other than the resolved root) and remind the user cleanup is **per repo** — do not loop automatically in Phase 1.

### Ordering

1. Python: `find_project_root` + `agent resolve` + tests.
2. Jinja partial + wire into lifecycle skills (init/close/cleanup/pick first — highest misroute risk).
3. Rule `.mdc` front matter + `_body.md.j2` note.
4. Design doc + README.
5. Run `verify_scaffold.py` + full pytest.

## Files to touch

| Path | Change |
| --- | --- |
| `src/issue_flow/project.py` | **New** — `find_project_root()` |
| `src/issue_flow/agent.py` | `run_resolve()` |
| `src/issue_flow/cli.py` | `agent resolve` subcommand |
| `src/issue_flow/gitutils.py` | Optional tiny helper if `resolve` needs shared origin fetch (likely reuse existing) |
| `src/issue_flow/templates/skills/_resolve_project_root.md.j2` | **New** partial |
| `src/issue_flow/templates/skills/iflow_{init,close,cleanup,pick,status,iflow,start,plan,pause,yolo,fix}/SKILL.md.j2` | Include partial; replace bare git/gh |
| `src/issue_flow/templates/commands/iflow-*.md.j2` | Same where not skill-delegated |
| `src/issue_flow/templates/rules/issueflow-rules.mdc.j2` | Scoped globs, `alwaysApply: false` |
| `src/issue_flow/templates/rules/_body.md.j2` | Multi-root subsection + link |
| `src/issue_flow/templates/docs/issue-workflow.md.j2` | Multi-root section |
| `src/issue_flow/templates/docs/this-project.md.j2` | Optional one-liner on toolchain doc |
| `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` | **New** design doc (this repo) |
| `README.md` | Short multi-root pointer |
| `tests/test_project.py` | **New** — root discovery |
| `tests/test_cli.py` | `agent resolve` JSON + edge cases |
| `tests/test_templating.py` | Assert partial included; `.mdc` globs; no regressed fast-path strings |

## Test strategy

```bash
uv run pytest tests/test_project.py tests/test_cli.py tests/test_templating.py tests/test_gitutils.py
uv run ruff check src/ tests/
uv run .issueflows/00-tools/verify_scaffold.py
```

- **Unit:** `find_project_root` — found at root, found walking up, none outside tree, respects custom `issueflows_dir` if configured.
- **CLI:** `agent resolve --json` on a throwaway scaffolded dir returns expected keys; `--from-file` nested path resolves to repo root; missing git returns graceful nulls consistent with `preflight`.
- **Templates:** render standard mode manifest; grep for mandated `--repo` / `-C` / `agent resolve` in updated skills; `issueflow-rules.mdc` has `alwaysApply: false` and non-empty `globs`.
- **Manual smoke (document in status):** two-folder Cursor workspace fixture; confirm `/iflow-init` with `root:` hint writes to correct `.issueflows/`.

## Open questions

1. **Phase boundary** — Confirm Phase 1 only for this PR (recommended), or pull `workspace.toml` (Phase 2) into #67?
2. **`repo:<folder-name>` matching** — Basename-only (e.g. `cellpy-core`) vs require `owner/repo` in Phase 1? Plan assumes **basename first**, full slug as override.
3. **AGENTS.md collisions** — Accept doc-only mitigation for Phase 1, or add a visible `<!-- issue-flow: {{ project_name }} -->` banner in the managed block so merged agents can disambiguate?
4. **Existing scaffolds** — Is `issue-flow update` sufficient to roll out scoped `.mdc` to cellpy/cellpy-core, or do you want a one-time note in the design doc about re-running update in each repo?

---

**Preflight (planning):** branch `67-multi-repo-cursor-workspaces-issue-flow-assumes-a-single-project-root` · 0 ahead / 0 behind `origin/main` · working tree dirty (`issue67_original.md`, this plan).
