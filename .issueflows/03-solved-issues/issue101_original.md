# Issue #101: Git hook integration — move issue files on commit by status markers

Source: https://github.com/jepegit/issue-flow/issues/101

## Original issue text

Optionally install a git pre-commit or post-commit hook that reads `issue<N>_status.md` files and moves the issue group between `01-current-issues/`, `02-partly-solved-issues/`, and `03-solved-issues/` based on the `- [x] Done` checkbox state.

**Context:** Mentioned in README.md [Future plans](https://github.com/jepegit/issue-flow/blob/main/README.md#future-plans).

**Acceptance criteria:**
- Opt-in during `issue-flow init` (e.g. `--install-hooks` flag)
- Hook script lives in `.issueflows/hooks/` and is symlinked into `.git/hooks/`
- Status-file parsing correctly identifies done vs not-done
- Hook coexists with existing project hooks (e.g. via Husky, pre-commit framework)
- README documents the hook behavior and how to enable/disable

**Questions:**
- Should this be a pre-commit or post-commit hook?
- How to handle conflicts with existing `.git/hooks/` files?
