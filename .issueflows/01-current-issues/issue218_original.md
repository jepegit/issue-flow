# Issue #218: doctor leftovers

Source: https://github.com/jepegit/issue-flow/issues/218

## Original issue text

When running iflow doctor, and then picking an issue, the agent responded:

```
Stop — dirty tree. Doctor cleanup still uncommitted on main:

Deleted: issue138_* from 01, issue100_* from 02
Untracked: same groups now under 03-solved-issues/
/iflow-pick needs clean tree before 142-… branch.

Options:

Commit housekeeping on main (e.g. chore: archive closed issueflow groups #100 #138), then branch + init
Stash, branch, init, leave stash for later
Abort
Which?
```

Since the doctor does not touch the actual code-base (?), we should allow commiting it as default?
