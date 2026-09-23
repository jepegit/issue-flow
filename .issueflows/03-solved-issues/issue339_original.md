# Issue #339: no iflow init in agents

Source: https://github.com/jepegit/issue-flow/issues/339

## Original issue text

Claude code was not able to pick up the issue flow skills (the init that should allow users to "register" issue-flow on the harness).

This is what I got inside my .agents/skills folder. And I typically run "issue-flow update" each time there is a new version of issue-flow (after installing the new version, off course). I thought we had that there so that I dont have to change from cursor issue-flow setup to the other harness inside the repo I am working on each time I switch harness. Is there some secret knob I have to turn on? 

```shell
❯ ls .agents/skills/
find-skills  herdr  herdr-nvim-follow  open-code-review  terminal-browser
```
