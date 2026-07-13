# Issue #102: GitHub Actions workflow — sync .issueflows/ state to GitHub labels/milestones

Source: https://github.com/jepegit/issue-flow/issues/102

## Original issue text

Ship a reusable GitHub Actions workflow that runs on push and syncs issue-file state between `.issueflows/` (current / parked / solved) and GitHub issue labels or milestones.

**Context:** Mentioned in README.md [Future plans](https://github.com/jepegit/issue-flow/blob/main/README.md#future-plans).

**Acceptance criteria:**
- Reusable workflow ships under `.github/workflows/issue-flow-sync.yml` or as a published action
- Workflow reads `issue<N>_status.md` files and applies labels (e.g. `status:current`, `status:parked`, `status:solved`)
- Alternatively, update the GitHub issue milestone based on folder location
- README documents how to enable and configure the workflow
- Example project uses the workflow successfully

**Questions:**
- Should sync be label-based, milestone-based, or both (configurable)?
- Should the workflow close GitHub issues when moved to `03-solved-issues/`?
- One-way sync (`.issueflows/` → GitHub) or bidirectional?
