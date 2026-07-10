# Plan — Issue #126: workspace issue flow

## Goal

In a multi-repo workspace, let the user declare a **default ("parent") repo**
that lifecycle commands target when invoked from outside any single scaffold
(e.g. the workspace root), via a small workspace registry file. This is the
`workspace.toml` registry already earmarked as Phase 2 in
`04-designs-and-guides/multi-repo-workspaces.md`.

## Constraints

- A single shared `.issueflows/` folder for the whole workspace stays
  **rejected** (see the design doc's "Alternatives considered"): GitHub issue
  numbers are a per-repo namespace, the lifecycle (branches/PRs) is per-repo
  regardless, and `/iflow-archive` recovery depends on the tracking files
  being committed in the repo that owns them.
- The workspace default must sit at the **bottom** of the existing resolution
  precedence: explicit `root:`/`repo:` hints, nearest scaffold, and the
  issue-branch heuristic all still win. The default only replaces the final
  "stop and ask" step. Nothing changes for projects without the file.
- Additive JSON: `agent resolve` keeps all existing fields.

## Approach

1. **Registry file** `issueflow-workspace.toml` at the workspace root:

   ```toml
   [workspace]
   default = "cellpy"                # member folder lifecycle commands default to
   members = ["cellpy", "cellpy-core"]  # optional; auto-discovered when omitted
   ```

2. **`project.py`**: `find_workspace_file()` (walk up, like
   `find_project_root`), `load_workspace()` (tomllib; members from config or
   auto-discovered as child dirs containing `.issueflows/`; `default_root()`
   validated to be a scaffolded member).
3. **`agent resolve`**: always report `workspace_root` / `workspace_default` /
   `workspace_members` when a registry is visible; when no scaffold is found
   by walking up, fall back to the workspace default
   (`resolved_via_workspace_default: true`).
4. **`issue-flow workspace init [DIR] [--default NAME] [--force] [--json]`**:
   materialize the registry with auto-discovered members; refuses to
   overwrite without `--force`.
5. **Templates**: `_resolve_project_root.md.j2` resolution order gains a
   "workspace default" step before "ask"; same one-liner in the rules body's
   multi-root section.
6. **Docs**: `docs/cli.md`, `docs/editors.md`, design doc Phase-2 status,
   `HISTORY.md`.

## Files to touch

- `src/issue_flow/project.py`, `agent.py`, `cli.py`
- `src/issue_flow/templates/skills/_resolve_project_root.md.j2`,
  `templates/rules/_body.md.j2`
- `tests/test_project.py`, `tests/test_cli.py`
- `docs/cli.md`, `docs/editors.md`,
  `.issueflows/04-designs-and-guides/multi-repo-workspaces.md`, `HISTORY.md`
- Regenerate repo scaffold (`scripts/update_issueflow_setup.py`)

## Test strategy

- Unit: workspace file walk-up; member auto-discovery vs explicit list;
  default validation (missing/unscaffolded default → ignored with note).
- CLI: `agent resolve` from workspace root falls back to default; from inside
  a member repo the nearest scaffold still wins; `workspace init` creates /
  refuses / forces.
- Template↔CLI consistency tests must keep passing (new `workspace` sub-app
  is introspected automatically).

## Open questions

- None blocking. Cross-repo `/iflow-pick` ranking and the multi-repo status
  dashboard remain follow-ups (Phases 3–4).
