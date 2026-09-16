# Issue #273: worktree tweak

Source: https://github.com/jepegit/issue-flow/issues/273

## Original issue text

Task 1: I have realized that I almost never want cursor to open a new window (it never works properly). Let us remove that option. 

Task 2: It seems I have to do a iflow cleanup for removing the worktree folder. If we are using worktrees, instead when we are in the iflow close part and it has made PR and the PR is merged, ask a simple YES/NO if worktree folder should be deleted (removed). Make it a know (auto-remove-worktree), default True. If knob on, always automatically remove worktree after succesfull merged PR / closed PR.
