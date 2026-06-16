# Issue #54: Allow for more interactive sessions

Source: https://github.com/jepegit/issue-flow/issues/54

## Original issue text

Sometimes we just need a branch to work on for smaller iterative fixes. We fix one small thing, use the code, find another small thing to fix etc; each one gets a short plan and then implements it if the user wants to. The changes should be recorded in the issue's corresponding markdown files.

## Comments (curated summary)

- **Additional tasks**: Introduce an interactive workflow (proposed command name `/issue-fix`) that supports a single long-lived branch for many small iterative fixes:
  1. User runs `/issue-fix <proposed name>`.
  2. Agent creates an issue (default name like `iterative-small-fixes` when none is given; it should preferably have a unique number) both on GitHub/GitLab and in `01-current-issues`, plus a branch for it. If not on `main`/`master`, ask whether to branch from the current branch or from `main`/`master`.
  3. During development, the agent updates the issue markdown file in `01-current-issues` when asked, and may proactively offer to update it when it sees fit.
  4. User finishes with `/issue-close`, running the normal issue-close procedure.
- **Clarifications / constraints**: Each small fix gets a short plan and is only implemented if the user wants it; all changes are recorded in the issue's corresponding markdown files.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-06-16._
