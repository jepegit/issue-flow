# Issue #45: include issue comments

Source: https://github.com/jepegit/issue-flow/issues/45

## Original issue text

It seems like issue-flow (during init) does not take into account additional comments to the issue. This is often not the wanted behaviour.

Task

1. improve "/issue-init" so that it also goes through the comments and include tasks from them (depending on the context, some comments might be downvoted or negated later on in the comment section). The comment section (added inside the _original.md file) does not have to be a 1-to-1 representation of the actual comments.
2. add another skill - describing how to review the comments and extract relevant tasks from them.
