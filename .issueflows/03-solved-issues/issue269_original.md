# Issue #269: system wide settings and update

Source: https://github.com/jepegit/issue-flow/issues/269

## Original issue text

If the user wants, the user should be able to set system wide issue-flow config and update all the issue-flow stacks the user has (all repos that use issue-flow on that computer). It should be possible to "lock" some repos if wanted (so, the config needs a way to mark an issue-flow containing repo as locked). Default is not locked.

## Stage 1 task list

- [x] #281 Design doc — user-global config, lock, registry, update-all
- [x] #282 Skill split — which packaged stems are global vs project-local



## Stage 2 — Config, lock, registry, update-all

- [x] #285 User-global config file + resolve precedence
- [x] #286 Per-repo lock flag
- [x] #287 Registry of issue-flowed projects + update-all


## Stage 3 — User-global skill materialize

- [x] #292 Confirm or skip opencode's user-global skill path
- [x] #293 Materialize both stems into per-editor user-global skill dirs

## Stage 4 — Registry hygiene + platform leftovers

- [x] #296 Dedupe workspace update and the registry
- [x] #297 Opt-in discover of `.issueflows/` trees
- [x] #298 Native Windows APPDATA tests (not a WSL bridge)

## Comments (curated summary)

- **Additional tasks**: install general skills globally, with a project copy where the skill is project-specific; register issue-flowed repos so updates can find them.
- **Clarifications / constraints**: stages 1–4 shipped that design. The later "unpublished leftovers" note was cleared by stage 4. The plan's Later section is empty.
- **Superseded / retracted**: none.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 3, last comment by @jepegit on 2026-09-17._
