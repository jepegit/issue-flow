# Issue #328: location of worktrees

Source: https://github.com/jepegit/issue-flow/issues/328

## Original issue text

I typically have larger projects inside a common workspace folder. For example, the folder cellpy-workspace contains all relevant repositories (cellpy, cellpy-core, cellpy-mcp, etc). When the agent creates a worktree folder, it puts it inside the cellpy-workspace folder. That is very good.

However, if I am working on a smaller project, and it contains only one repository, I typically dont want the agent to create a worktree folder in that repos parent folder. But instead inside a dedicated folder for general worktrees (probably called "worktrees")

So, we need a setting / knob that allows users to define a common worktrees folder. And a knob that turns on or off creating worktrees inside workspace folders provided that the repo is inside a workspace folder, off coures. If not, we use the common worktrees folder. If worktrees folder does not exist, or the user opts out of having one (knob), then we do as we do currently (put the worktree folder alongside the repo folder).
