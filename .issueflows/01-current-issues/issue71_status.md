# Status for Issue #71: Rename issue-* slash commands to a shorter, more consistent scheme

## What has been done

All implementation tasks from the plan have been completed:

1. ✅ Updated `COMMAND_NAMES` and `SKILL_DIRS` in `templating.py` with new `iflow-*` names
2. ✅ Added `RETIRED_COMMANDS` and `RETIRED_SKILLS` lists for pruning old files
3. ✅ Renamed all 11 command template files from `issue-*` to `iflow-*`
4. ✅ Renamed all 15 skill template folders from `issueflow_*` to `iflow_*`
5. ✅ Updated cross-references in all command templates
6. ✅ Updated cross-references in all skill templates (frontmatter + content)
7. ✅ Updated cross-references in rules templates (`_body.md.j2`)
8. ✅ Updated cross-references in docs template (`issue-workflow.md.j2`)
9. ✅ Updated `tests/test_templating.py` with new command/skill names
10. ✅ Updated `tests/test_init.py` with new command/skill names
11. ✅ Updated `tests/test_update.py` and `tests/test_cli.py` with new command/skill names
12. ✅ Updated `README.md` with new command/skill names
13. ✅ Updated `AGENTS.md` manual section
14. ✅ Implemented pruning logic in `init.py` to remove retired files
15. ✅ All 147 tests passing

## Naming decisions

- **Option C confirmed**: Used `iflow-` prefix for all commands
- **Graphify included**: Renamed `/graphify` → `/iflow-graphify` for family consistency
- **Skills simplified**: Changed from `issueflow-issue-*` to `iflow-*` (removed redundancy)
- **Pruning implemented**: Automatic removal of old files during `issue-flow update`

## Key changes

### Commands renamed:
- `issue-pick` → `iflow-pick`
- `issue-init` → `iflow-init`
- `issue-plan` → `iflow-plan`
- `issue-start` → `iflow-start`
- `issue-pause` → `iflow-pause`
- `issue-close` → `iflow-close`
- `issue-cleanup` → `iflow-cleanup`
- `issue-yolo` → `iflow-yolo`
- `issue-fix` → `iflow-fix`
- `issue-status` → `iflow-status`
- `graphify` → `iflow-graphify`

### Skills renamed:
- `issueflow-issue-*` → `iflow-*`
- `issueflow-version-bump` → `iflow-version-bump`
- `issueflow-history-update` → `iflow-history-update`
- `issueflow-graphify` → `iflow-graphify`
- `issueflow-iflow` → `iflow-iflow`

## Test results

All 147 tests pass successfully:
- Template rendering tests ✅
- Manifest integrity tests ✅
- Cross-reference consistency tests ✅
- Multi-editor tests (Cursor, Claude, Codex, OpenCode) ✅
- Pruning logic tests ✅

## Remaining work

- [x] Done

All implementation complete, tested, and ready to merge.
