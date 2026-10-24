# Issue #268: Improve skills

Source: https://github.com/jepegit/issue-flow/issues/268

## Original issue text

There has been some development on how to write skills. Search web, and in particular our sources/references and find updated information. Check if our skills can be improved. If so, improve.

## Comments (curated summary)

- **Additional tasks**:
  - Add a mechanical Agent Skills lint: `name` matches `^[a-z0-9]+(-[a-z0-9]+)*$`, `name` + `description` required, frontmatter `name` equals the directory name, `description` ≤ 1024 chars, warning on long bodies.
  - Review the YouTube video https://www.youtube.com/watch?v=n9CSSSir3fE and apply its relevant lessons to the issue-flow skills.
- **Clarifications / constraints**:
  - The lint allowlist must include the issue-flow frontmatter keys (`disable-model-invocation`, `issue-flow-version`), so they are not flagged as unknown.
  - The 500-line body hint is not an error for lifecycle skills (a warning at most).
  - Surface: `issue-flow doctor` or a small `issue-flow lint-skills`. Decide in the plan.
  - Cite writing-great-skills and `skill-authoring.md`; source context is #275 and `.issueflows/04-designs-and-guides/skillbook-lessons.md`. Keep it inside this issue (no new issue).

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 2, last comment by @jepegit on 2026-09-23._
