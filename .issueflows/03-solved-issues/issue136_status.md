# Status — Issue #136: /iflow-epic skill + 05-epics scaffold (draft-only)

- [x] Done

## Checklist

- [x] config.py: `epics_folder = "05-epics"` + subdirs + template context
- [x] templating.py: `iflow-epic` command stem + `iflow_epic` skill stem
- [x] step_profiles.toml: `iflow_epic = "reasoning"`
- [x] iflow_epic skill template (draft-only playbook, parseable plan
      structure, sizing rules, yolo-fitness judgments) + command twin
- [x] Off-path enumerations: dispatcher skill + command, workflow doc table
      (+ dispatcher row), rules body paragraph
- [x] Tests: 3 new epic-surface tests; folder/gitkeep/manifest/context-count
      tests updated (429 passed)
- [x] HISTORY entry; scaffold regenerated

## Notes

The plan-file structure (`### Issue:` specs, `Depends on:` lines with
`stage <j> issue <k>` placeholders, `Status: draft|confirmed`) is the parsing
contract #137 (publish) and #138 (epic-status CLI) build on.
