# Issue #25: improve the issue close functionality

Source: https://github.com/jepegit/issue-flow/issues/25

## Original issue text

Enhance `/issue-close` so that it notifies the user if there are uncommitted changes (that issueflow has decided are not relevant for the issue) and asks if they also should be committed.

Also, after creating the PR, notify to the user that they are not on the main branch (so that the user does not accidentally start doing stuff on the issue branch if they not actually want to do that)
