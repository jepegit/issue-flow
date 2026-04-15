# Issue #4: update issueflow for already initialized projects

Source: https://github.com/jepegit/issue-flow/issues/4

## Original issue text

Since `issue-flow` is constantly improving (at least constantly changing), we need to make it easy for users to update their already initialized projects.

1. If running `issueflow init` in a repo/project that has already been initialized, make sure that the content that it is likely the user would like to keep (like issue statuses and descriptions) is not destroyed.
2. add a subcommand `issueflow update` that updates the issueflow commands, etc. (for example, a newer version of issue-flow might need more folders).
