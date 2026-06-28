# Issue #82: switch back to main if clean

Source: https://github.com/jepegit/issue-flow/issues/82

## Original issue text

The "/iflow-close" should automatically switch back to the main branch (typically main or master) after the PR if all changes were included in the PR (i.e. it should off course not switch if there are uncommited changes etc). If this behaviour is not wanted, the user should append something like "stay" or "dont switch to main". For example: "/iflow-close stay".
