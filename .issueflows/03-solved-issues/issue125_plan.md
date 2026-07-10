# Plan — Issue #125: version bump skill must be more flexible

## Goal

`iflow-version-bump` (and the `/iflow-close` bump step) must handle projects
whose version is **derived from git tags** (setuptools-scm / hatch-vcs /
versioningit), not only projects with a static `[project] version` bumped via
`uv version --bump`. In cellpy the skill's advice was actively wrong.

## Constraints

- Existing static-uv behaviour (levels table, pre-release-aware default) is
  unchanged and stays the final default — existing tests assert its wording.
- Tag-based projects: **never** write a version into `pyproject.toml`, and
  **never tag an issue-branch commit** — in a squash-merge world the tagged
  commit would not land on the default branch. Tagging happens after merge.
- `this-project.md` is user-owned: `init`/`update` never overwrite it, so the
  new section only appears in *new* briefs; agents repair existing briefs.

## Approach

Strategy resolution order (mirrors the toolchain-deference pattern):

1. **`this-project.md` "Release & version bump" section** — user-owned, wins.
2. **Auto-detect from `pyproject.toml`** — `dynamic = ["version"]` plus a
   known backend (`[tool.setuptools_scm]`, `hatch-vcs`, `versioningit`, …)
   → tag-based; static `[project] version` → uv.
3. **Default** — current uv behaviour.

Changes:

- `templates/docs/this-project.md.j2`: new "Release & version bump" section
  (TODO + a worked example per strategy).
- `templates/skills/iflow_version_bump/SKILL.md.j2`: strategy resolution
  first; static-uv path unchanged; new tag-based path (next version computed
  from the latest tag with the same level table; close only *plans* the tag;
  creation deferred to post-merge); **self-healing step**: record a
  discovered/clarified strategy into `this-project.md`.
- Close templates (skill + command): bump step defers to the strategy; for
  tag-based, report the planned tag, promote `HISTORY.md` with the planned
  version, and (yolo only) create the tag after the post-merge pull.
- Cleanup templates (skill + command): the consolidated confirm may include
  creating the planned-but-missing release tag once on the merged default
  branch; constraints amended accordingly.
- Workflow doc template + repo design note; tests in `test_init.py`.

## Files to touch

- `src/issue_flow/templates/docs/this-project.md.j2`
- `src/issue_flow/templates/skills/iflow_version_bump/SKILL.md.j2`
- `src/issue_flow/templates/skills/iflow_close/SKILL.md.j2`,
  `templates/commands/iflow-close.md.j2`
- `src/issue_flow/templates/skills/iflow_cleanup/SKILL.md.j2`,
  `templates/commands/iflow-cleanup.md.j2`
- `src/issue_flow/templates/docs/issue-workflow.md.j2`
- `tests/test_init.py`, `.issueflows/04-designs-and-guides/`, `HISTORY.md`
- Regenerated scaffold

## Test strategy

Template-contract tests (test_init style): the starter brief contains the
release section; the rendered version-bump skill documents the resolution
order, tag detection markers, and the never-tag-before-merge rule; the close
skill mentions the planned-tag deferral; existing uv-wording tests keep
passing.

## Open questions

- Deterministic `issue-flow agent version-plan` CLI (PEP 440 next-version
  arithmetic for tag projects) is deliberately deferred to a follow-up.
