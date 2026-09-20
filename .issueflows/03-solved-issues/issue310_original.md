# Issue #310: need a global iflow initialisation command

Source: https://github.com/jepegit/issue-flow/issues/310

## Original issue text

Current behaviour.
```
  write .cursor/skills/iflow-auto/SKILL.md
  write .cursor/skills/iflow-drive/SKILL.md
  write .cursor/skills/iflow-version-bump/SKILL.md
  write .cursor/skills/iflow-history-update/SKILL.md
  write .cursor/skills/iflow-graphify/SKILL.md
  write .cursor/skills/caveman/SKILL.md
  write .cursor/skills/grill-me/SKILL.md
  write .cursor/skills/gh-ci/SKILL.md
  write .cursor/rules/issueflow-rules.mdc
  write docs/issue-workflow.md
  write AGENTS.md  (issue-flow managed block)

User-global both skills
  write cursor:/home/jepe/.cursor/skills/caveman/SKILL.md
  write cursor:/home/jepe/.cursor/skills/grill-me/SKILL.md
  write cursor:/home/jepe/.cursor/skills/gh-ci/SKILL.md


Graphify integration
  run   graphify cursor install
  ok    graphify cursor skill registered

Refreshed 36 file(s).
```

I prefer to create a common folder for all related repos. Therefore I need a global iflow initialisation skill
