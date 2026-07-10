# Status — Issue #125: version bump skill must be more flexible

- [x] Done

## Current status

Implemented on branch `125-version-bump-strategy`. The version-bump skill is
now release-strategy-aware: the "Release & version bump" section of
`this-project.md` wins, else detection from `pyproject.toml`
(`dynamic = ["version"]` + tag backend → git-tag strategy), else the
unchanged uv default. Tag-derived projects get a **planned tag** at close
time and the actual tag after the merge (cleanup, or yolo post-merge) —
never on the issue branch.

## Checklist

- [x] `this-project.md.j2`: Release & version bump section (starter briefs)
- [x] `iflow-version-bump` skill: strategy resolution, tag-derived path,
      self-healing "record what you learn" step; static uv path unchanged
- [x] Close templates (skill + command): strategy-aware bump step, planned-tag
      deferral, HISTORY promotion with planned version, yolo post-merge tag
- [x] Cleanup templates (skill + command): planned-tag creation in the
      consolidated confirm; constraints amended
- [x] Workflow doc template updated; design note
      `04-designs-and-guides/release-strategies.md`; repo's own brief gained
      its release section (static uv)
- [x] Tests: 4 new template-contract tests in `test_init.py`; full suite 384
      passed
- [x] Scaffold regenerated

## Remaining work

None. Follow-up candidate (deliberately out of scope): deterministic
`issue-flow agent version-plan` CLI doing the PEP 440 next-tag arithmetic.
