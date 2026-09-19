# Issue #306: pick issue then create epic then publish auto all

Source: https://github.com/jepegit/issue-flow/issues/306

## Original issue text

Implement following flow:

1) creates epic from an issue (default is automatically accept all, unless grill-me is given)
2) implements the whole epic using publish, auto on each part, keeps track of new issues found
3) performs a review of what has been done after the full epic is finished and creates the issues on github (if any new issues found)
4) performs a cleanup (only local and only -d)
5) reports to user what has been done, preforms an iflow-status

The flow should be able to abort if the user sends "abort" or similar message
