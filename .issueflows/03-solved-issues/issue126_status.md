# Status — Issue #126: workspace issue flow

- [x] Done

## Current status

Implemented on branch `126-workspace-registry`. A shared top-level
`.issueflows/` stays rejected (per the multi-repo design doc); instead the
workspace registry `issueflow-workspace.toml` declares a default ("parent")
member repo that fills only the final "stop and ask" step of the resolution
order.

## Checklist

- [x] `project.py`: `find_workspace_file` / `load_workspace` /
      `discover_workspace` (+ `WORKSPACE_FILENAME`)
- [x] `agent resolve`: workspace fields + default fallback
      (`resolved_via_workspace_default`)
- [x] `issue-flow workspace init [--default MEMBER] [--force] [--json]`
- [x] Template updates: `_resolve_project_root.md.j2` resolution order,
      rules `_body.md.j2` multi-root section, `issue-workflow.md.j2`
- [x] Tests: 7 unit (test_project.py) + 8 CLI (test_cli.py); full suite 380
      passed; template↔CLI consistency tests cover the new sub-app
- [x] Docs: `docs/cli.md`, `docs/editors.md`, design doc Phase-2 section,
      `HISTORY.md`
- [x] Scaffold regenerated (`scripts/update_issueflow_setup.py`)
- [x] E2E sandbox: `workspace init` + resolve fallback from workspace root
      (default used) and from inside a member (nearest scaffold wins)

## Remaining work

None. Ready for commit / PR (`Closes #126`).
