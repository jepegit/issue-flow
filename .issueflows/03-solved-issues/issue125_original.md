# Issue #125: version bump skill must be more flexible

Source: https://github.com/jepegit/issue-flow/issues/125

## Original issue text

In one of my repos (cellpy), I got this message when asking the agent why uv release --bump alpha did not work:

```text
Create a new git tag (your latest alpha is v1.0.4a2):

git tag v1.0.4a3
# or cut a GitHub release:
gh release create v1.0.4a3 --target master --generate-notes
The built package version will then reflect that tag.

Note: The issue-flow docs and .cursor/skills/iflow-version-bump/SKILL.md still describe uv version --bump â€¦, which fits projects with a static version = "..." line. For cellpy, that step is outdated â€” bumping means tagging, not editing pyproject.toml.
```

This means that the skill in my cellpy project is not aligned with how bumping should be done for cellpy. Can we include something in the skill that takes care of this. Maybe we could add the "bumping / release strategy" as a part (chapter) of `this-project.md` and that the skill selects bumping / release method from` this-project.md` if it is filled in?
