# Issue #211: option C problem

Source: https://github.com/jepegit/issue-flow/issues/211

## Original issue text

The agent seems to want to run the `issue-flow agent capture` with the -C flag. However, this option does not exist. Why, and how to fix it? 


```
issue-flow agent capture 651 -C "c:/scripting/cellpy-workspace/cellpy" --repo jepegit/cellpy && issue-flow agent sweep --except 651 -C "c:/scripting/cellpy-workspace/cellpy" && gh issue view 651 --repo jepegit/cellpy --json title,body,url,number,comments
wrote  
C:\scripting\cellpy-workspace\cellpy\.issueflows\01-current-issues\issue651_orig
inal.md
Usage: issue-flow agent sweep [OPTIONS] [project_dir]
Try 'issue-flow agent sweep --help' for help.
┌─ Error ──────────────────────────────────────────────────────────────────────┐
│ No such option: -C                                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```
