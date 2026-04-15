# Issue #2: Enhance issue-init so that it selects issue related to current branch if no issue number is given

Source: https://github.com/jepegit/issue-flow/issues/2

## Original issue text

the command /issue-init expects at minimum an issue number before starting. If we already are on a branch, and it is created from an issue (has the branch name NN-issue-text) it will often be the case that the issue NN is the one the user wants to work on.

To be in line with the simplicity principle, the agent should ask something like "you have not provided any issue reference, should I look for issues related to the current branch?

Sometimes it is an obvious mistake from the user (just forgot it), for example if the branch is called main or master. Then it is no point in continuing, just inform the user that, sorry, you cant continue until we know what issue we are working on.
