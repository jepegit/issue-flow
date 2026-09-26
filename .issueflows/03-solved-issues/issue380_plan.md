# Plan — Issue #380: PowerShell-safe multi-line gh bodies

## Goal

Skills and agent docs that create multi-line GitHub text must say to use
`--body-file` (or `git commit -F`). Bash `<<'EOF'` heredocs fail in
Windows PowerShell.

## Approach

One shared snippet, `skills/_gh_body_file.md.j2`, included from every
skill and command that creates an issue or a PR body. Same note on the
agent how-to, the write-an-issue page, `llms.txt`, and the command
reference for `/iflow-issue`. No shell detector and no CLI rewriter.

## Files to touch

- `src/issue_flow/templates/skills/_gh_body_file.md.j2` (new)
- Issue, fix, pick, split, epic, cleanup, close, build, and auto
  skill + command templates
- `docs/how-to/for-agents.md`, `docs/how-to/write-an-issue.md`,
  `docs/llms.txt`
- `src/issue_flow/templates/docs/issue-workflow.md.j2`
- `tests/test_templating.py`
- Re-render with `issue-flow update`

## Test strategy

Template render asserts `/iflow-issue` skill and command contain
`--body-file` and `PowerShell`. Full pytest before close.
