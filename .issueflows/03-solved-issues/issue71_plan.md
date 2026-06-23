# Plan for Issue #71: Rename issue-* slash commands to a shorter, more consistent scheme

## Goal

Rename the `issue-*` command family to `iflow-*` so the dispatcher `/iflow` becomes the namespace root and all workflow commands share a consistent, on-brand prefix that ties to the project name (issue-flow → iflow).

## Constraints

- Must maintain the same functionality — this is purely a rename, not a behavior change
- Breaking change to the user-facing command surface → requires clear communication
- Migration path must handle existing installations gracefully
- All cross-references between commands/skills/docs must stay consistent
- Test manifest counts remain 29 (12 commands + 15 skills + 1 rule + 1 doc) — no additions, just renames

## Prior-art discovery

**God Nodes (from GRAPH_REPORT.md):**
- `templating.py` (degree 10) — holds `COMMAND_NAMES` and `SKILL_DIRS` manifests
- `test_templating.py` (degree 7) — hardcoded expected command/skill lists
- Command/skill template cross-references throughout

**Key files identified:**
- Core manifest: `src/issue_flow/templating.py`
- Template files: 12 command templates + 15 skill templates + 3 rules templates + 1 doc template
- Tests: `tests/test_templating.py`
- Documentation: `README.md`, `AGENTS.md` (managed block), `docs/issue-workflow.md` (template)

**Cross-reference patterns found:**
- `/iflow` lists all linear and off-path commands
- `/issue-yolo`, `/issue-pick`, `/issue-fix` reference sibling commands
- `/issue-close` points to `/issue-cleanup`
- All skills mirror their respective commands
- Rules template describes command lifecycle

### Prior art

None found (grep + graph checked) — this is the first comprehensive command rename.

## Approach

### Phase 1: Decisions on open questions

**Q1: Confirm option C (`iflow-`) vs option B (`if-`)?**
→ **Decision:** Option C (`iflow-`). While not shorter, it's consistent, on-brand, and avoids the `if`-keyword ambiguity. Brevity is less important than clarity for long-term maintainability.

**Q2: Does `graphify` join the family as `iflow-graphify`?**
→ **Decision:** **Yes, rename to `iflow-graphify`**. While it wraps an external tool, it's already part of the workflow manifest and has a mirrored skill. Consistency wins. The CLI subcommand `issue-flow graphify` stays unchanged.

**Q3: Migration strategy (document / prune / alias)?**
→ **Decision:** **Prune on update** (option 2). When `issue-flow update` runs, detect and delete the old `issue-*` command files and old `issueflow-issue-*` skill folders. This gives the cleanest UX with no manual cleanup required. Implementation:
- Add a `RETIRED_COMMANDS` list in `templating.py` with old names
- Add a `RETIRED_SKILLS` list in `templating.py` with old folder names
- In `init.py`, after writing the new files, delete any retired ones found in `agent_dir`

### Phase 2: Rename template files

**Command templates** (`src/issue_flow/templates/commands/`):
- `issue-pick.md.j2` → `iflow-pick.md.j2`
- `issue-init.md.j2` → `iflow-init.md.j2`
- `issue-plan.md.j2` → `iflow-plan.md.j2`
- `issue-start.md.j2` → `iflow-start.md.j2`
- `issue-pause.md.j2` → `iflow-pause.md.j2`
- `issue-close.md.j2` → `iflow-close.md.j2`
- `issue-cleanup.md.j2` → `iflow-cleanup.md.j2`
- `issue-yolo.md.j2` → `iflow-yolo.md.j2`
- `issue-fix.md.j2` → `iflow-fix.md.j2`
- `issue-status.md.j2` → `iflow-status.md.j2`
- `graphify.md.j2` → `iflow-graphify.md.j2`
- `iflow.md.j2` → (no rename, already correct)

**Skill template folders** (`src/issue_flow/templates/skills/`):
- `issueflow_issue_pick/` → `iflow_pick/`
- `issueflow_issue_init/` → `iflow_init/`
- `issueflow_issue_comments/` → `iflow_comments/`
- `issueflow_issue_plan/` → `iflow_plan/`
- `issueflow_issue_start/` → `iflow_start/`
- `issueflow_issue_pause/` → `iflow_pause/`
- `issueflow_issue_close/` → `iflow_close/`
- `issueflow_issue_cleanup/` → `iflow_cleanup/`
- `issueflow_issue_yolo/` → `iflow_yolo/`
- `issueflow_issue_fix/` → `iflow_fix/`
- `issueflow_issue_status/` → `iflow_status/`
- `issueflow_version_bump/` → `iflow_version_bump/`
- `issueflow_history_update/` → `iflow_history_update/`
- `issueflow_graphify/` → `iflow_graphify/`
- `issueflow_iflow/` → `iflow_iflow/` (consistent pattern: skill folders stay underscored)

### Phase 3: Update manifest lists

**`src/issue_flow/templating.py`:**

1. Update `COMMAND_NAMES` list (lines 75-88):
```python
COMMAND_NAMES: list[str] = [
    "iflow",
    "iflow-pick",
    "iflow-init",
    "iflow-plan",
    "iflow-start",
    "iflow-pause",
    "iflow-close",
    "iflow-cleanup",
    "iflow-yolo",
    "iflow-fix",
    "iflow-status",
    "iflow-graphify",
]
```

2. Update `SKILL_DIRS` list (lines 93-109):
```python
SKILL_DIRS: list[str] = [
    "iflow_iflow",
    "iflow_pick",
    "iflow_init",
    "iflow_comments",
    "iflow_plan",
    "iflow_start",
    "iflow_pause",
    "iflow_close",
    "iflow_cleanup",
    "iflow_yolo",
    "iflow_fix",
    "iflow_status",
    "iflow_version_bump",
    "iflow_history_update",
    "iflow_graphify",
]
```

3. Add retired names lists for pruning:
```python
# Retired command names (pre-v0.5.0 rename) to be removed on update
RETIRED_COMMANDS: list[str] = [
    "issue-pick",
    "issue-init",
    "issue-plan",
    "issue-start",
    "issue-pause",
    "issue-close",
    "issue-cleanup",
    "issue-yolo",
    "issue-fix",
    "issue-status",
    "graphify",
]

# Retired skill folder names (pre-v0.5.0 rename) to be removed on update
RETIRED_SKILLS: list[str] = [
    "issueflow-issue-pick",
    "issueflow-issue-init",
    "issueflow-issue-comments",
    "issueflow-issue-plan",
    "issueflow-issue-start",
    "issueflow-issue-pause",
    "issueflow-issue-close",
    "issueflow-issue-cleanup",
    "issueflow-issue-yolo",
    "issueflow-issue-fix",
    "issueflow-issue-status",
    "issueflow-version-bump",
    "issueflow-history-update",
    "issueflow-graphify",
    "issueflow-iflow",
]
```

### Phase 4: Update cross-references in templates

**Commands that reference siblings:**

1. **`iflow.md.j2`** — lists all commands in dispatch table and off-path section:
   - Replace all `/issue-*` → `/iflow-*`
   - Replace `/graphify` → `/iflow-graphify`

2. **`iflow-pick.md.j2`** — references `/issue-init`, `/issue-plan`:
   - `/issue-init` → `/iflow-init`
   - `/issue-plan` → `/iflow-plan`

3. **`iflow-init.md.j2`** — references `issueflow-issue-comments` skill:
   - `issueflow-issue-comments` → `iflow-comments`

4. **`iflow-plan.md.j2`** — references `/issue-start`:
   - `/issue-start` → `/iflow-start`

5. **`iflow-start.md.j2`** — references `/issue-plan`:
   - `/issue-plan` → `/iflow-plan`

6. **`iflow-close.md.j2`** — references `/issue-cleanup`, skills:
   - `/issue-cleanup` → `/iflow-cleanup`
   - `issueflow-history-update` → `iflow-history-update`
   - `issueflow-version-bump` → `iflow-version-bump`

7. **`iflow-cleanup.md.j2`** — (no sibling references)

8. **`iflow-yolo.md.j2`** — references all four linear commands + cleanup:
   - `/issue-init` → `/iflow-init`
   - `/issue-plan` → `/iflow-plan`
   - `/issue-start` → `/iflow-start`
   - `/issue-close` → `/iflow-close`
   - `/issue-cleanup` → `/iflow-cleanup`

9. **`iflow-fix.md.j2`** — references `/issue-init`, `/issue-close`, `/iflow`:
   - `/issue-init` → `/iflow-init`
   - `/issue-close` → `/iflow-close`
   - `/iflow` → (already correct)

10. **`iflow-pause.md.j2`** — (no sibling references)

11. **`iflow-status.md.j2`** — (no sibling references)

12. **`iflow-graphify.md.j2`** — references `/iflow`, `/issue-start`, `/issue-close`:
    - `/issue-start` → `/iflow-start`
    - `/issue-close` → `/iflow-close`

**Skills that reference siblings** (all 15 skill `SKILL.md.j2` files):
- Same cross-reference patterns as their respective commands
- Update `name:` frontmatter in each skill file from `issueflow-*` to `iflow-*`

**Rules templates:**

1. **`rules/_body.md.j2`** — the shared "Command lifecycle" section:
   - Replace all `/issue-*` → `/iflow-*`
   - Replace `/graphify` → `/iflow-graphify`

2. **`rules/issueflow-rules.mdc.j2`** — includes `_body.md.j2`

3. **`rules/AGENTS.md.j2`** — includes `_body.md.j2`

4. **`rules/CLAUDE.md.j2`** — includes `_body.md.j2`

**Documentation template:**

1. **`docs/issue-workflow.md.j2`** — command/skill tables and per-command sections:
   - Replace all `/issue-*` → `/iflow-*`
   - Replace all `issueflow-issue-*` → `iflow-*`
   - Replace `issueflow-version-bump` → `iflow-version-bump`
   - Replace `issueflow-history-update` → `iflow-history-update`
   - Replace `issueflow-graphify` → `iflow-graphify`
   - Replace `issueflow-iflow` → `iflow-iflow`
   - Replace `/graphify` → `/iflow-graphify`

### Phase 5: Update project documentation

**`README.md`:**
- Update tree listing (lines ~19-48): all command/skill paths
- Update command descriptions (~lines 56-72): all `/issue-*` → `/iflow-*`, `/graphify` → `/iflow-graphify`
- Update skill mentions (~line 73): all `issueflow-*` → `iflow-*`
- Update any other prose mentioning the old names

**`AGENTS.md`:**
- The managed block (`<!-- BEGIN issue-flow ... END issue-flow -->`) is auto-updated by `issue-flow update`, so changes here will propagate automatically once templates are updated
- Manual section above the managed block: update any `/issue-*` → `/iflow-*` references

### Phase 6: Update tests

**`tests/test_templating.py`:**

1. Update hardcoded command list in `test_manifest_has_expected_commands_and_skills()` (lines 146-178):
   - Replace all `issue-*` → `iflow-*`
   - Replace `graphify` → `iflow-graphify`
   - Replace all `issueflow_issue_*` → `iflow_*`
   - Replace `issueflow_version_bump` → `iflow_version_bump`
   - Replace `issueflow_history_update` → `iflow_history_update`
   - Replace `issueflow_graphify` → `iflow_graphify`
   - Replace `issueflow_iflow` → `iflow_iflow`

2. Update `test_template_substitution()` (line 48):
   - `commands/issue-init.md.j2` → `commands/iflow-init.md.j2`

3. Update `test_resolve_output_path()` (line 55):
   - `issue-init.md` → `iflow-init.md`

4. Update `test_build_manifest_opencode_uses_singular_command_dir()` (line 98):
   - `issue-init.md` → `iflow-init.md`
   - `issueflow-issue-init` → `iflow-init`

5. Update `test_build_manifest_claude_emits_claude_md_and_commands()` (line 109):
   - `issue-init.md` → `iflow-init.md`

6. Update all other test functions that reference command/skill names:
   - Search for `/issue-` and replace with `/iflow-`
   - Search for `issueflow-issue-` and replace with `iflow-`
   - Search for `issueflow-` (remaining) and replace with `iflow-`

### Phase 7: Implement pruning logic

**`src/issue_flow/init.py`:**

Add a cleanup function to remove retired files after writing the new manifest. This should:

1. Import `RETIRED_COMMANDS` and `RETIRED_SKILLS` from `templating.py`
2. After writing all templates, iterate through retired names
3. For each retired command: check if `{agent_dir}/commands/{name}.md` exists and delete it
4. For each retired skill: check if `{agent_dir}/skills/{name}/` exists and recursively delete the folder
5. Log what was pruned (for user visibility)

Implementation sketch:
```python
def prune_retired_files(agent_dir: Path, commands_dir: str | None) -> None:
    """Remove pre-v0.5.0 command and skill files after update."""
    from issue_flow.templating import RETIRED_COMMANDS, RETIRED_SKILLS
    
    pruned = []
    
    if commands_dir:
        cmd_dir = agent_dir / commands_dir
        for old_name in RETIRED_COMMANDS:
            old_file = cmd_dir / f"{old_name}.md"
            if old_file.exists():
                old_file.unlink()
                pruned.append(str(old_file.relative_to(Path.cwd())))
    
    skills_dir = agent_dir / "skills"
    for old_skill in RETIRED_SKILLS:
        old_folder = skills_dir / old_skill
        if old_folder.exists():
            import shutil
            shutil.rmtree(old_folder)
            pruned.append(str(old_folder.relative_to(Path.cwd())))
    
    if pruned:
        print(f"Pruned {len(pruned)} retired files from pre-v0.5.0:")
        for p in pruned:
            print(f"  - {p}")
```

Call this from `write_manifests()` or similar, after the new files are written.

## Files to touch

### Core implementation
1. `src/issue_flow/templating.py` — update manifests, add retired lists
2. `src/issue_flow/init.py` — add pruning logic

### Template files (31 total)
**Commands (12):**
3. Rename `src/issue_flow/templates/commands/issue-pick.md.j2` → `iflow-pick.md.j2` + update cross-refs
4. Rename `src/issue_flow/templates/commands/issue-init.md.j2` → `iflow-init.md.j2` + update cross-refs
5. Rename `src/issue_flow/templates/commands/issue-plan.md.j2` → `iflow-plan.md.j2` + update cross-refs
6. Rename `src/issue_flow/templates/commands/issue-start.md.j2` → `iflow-start.md.j2` + update cross-refs
7. Rename `src/issue_flow/templates/commands/issue-pause.md.j2` → `iflow-pause.md.j2` + update cross-refs
8. Rename `src/issue_flow/templates/commands/issue-close.md.j2` → `iflow-close.md.j2` + update cross-refs
9. Rename `src/issue_flow/templates/commands/issue-cleanup.md.j2` → `iflow-cleanup.md.j2` + update cross-refs
10. Rename `src/issue_flow/templates/commands/issue-yolo.md.j2` → `iflow-yolo.md.j2` + update cross-refs
11. Rename `src/issue_flow/templates/commands/issue-fix.md.j2` → `iflow-fix.md.j2` + update cross-refs
12. Rename `src/issue_flow/templates/commands/issue-status.md.j2` → `iflow-status.md.j2` + update cross-refs
13. Rename `src/issue_flow/templates/commands/graphify.md.j2` → `iflow-graphify.md.j2` + update cross-refs
14. Update `src/issue_flow/templates/commands/iflow.md.j2` (no rename, update cross-refs only)

**Skills (15 folders, each with SKILL.md.j2):**
15-29. Rename all 15 skill folders + update frontmatter `name:` and cross-refs in each SKILL.md.j2

**Rules (3, shared body):**
30. Update `src/issue_flow/templates/rules/_body.md.j2` (cross-refs)
31. (rules/issueflow-rules.mdc.j2, rules/AGENTS.md.j2, rules/CLAUDE.md.j2 inherit from _body)

**Docs (1):**
32. Update `src/issue_flow/templates/docs/issue-workflow.md.j2`

### Tests
33. `tests/test_templating.py` — update all hardcoded command/skill names

### Project docs
34. `README.md` — update tree listing, command descriptions, skill mentions
35. `AGENTS.md` — update manual section (managed block auto-updates)

## Test strategy

1. **Template rendering:** All existing tests in `test_templating.py` should pass after name updates
2. **Manifest integrity:** Verify `test_manifest_entry_count()` still reports 29
3. **Cross-reference consistency:** Render all templates and grep for lingering old names:
   - No `/issue-` (except in comments/examples where explicitly discussing the rename)
   - No `issueflow-issue-`
   - No bare `issueflow-` (except in test contexts)
4. **Pruning logic:** Test that retired files are detected and removed (add unit test or manual verification)
5. **Full integration:** Run `issue-flow init --editor cursor` in a test directory and verify:
   - All new command files are created with `iflow-*` names
   - All new skill folders use `iflow-*` names
   - No old `issue-*` files are left behind
6. **Update scenario:** Create old files manually, then run `issue-flow update` and verify they're pruned

## Open questions

1. **Pruning announcement:** Should `issue-flow update` print a summary of pruned files, or stay silent?
   → **Decision in plan:** Print a summary (helps users understand what changed).

2. **Version bump magnitude:** Minor (0.4.x → 0.5.0) or major (1.0.0)?
   → **Decision:** Minor (0.5.0), as indicated by the milestone. Major bump can wait for 1.0 stabilization.

3. **HISTORY.md entry timing:** Draft it now in the plan, or wait for `/issue-close`?
   → **Decision:** Draft a placeholder here for review, finalize at close time.

**Placeholder HISTORY.md entry:**
```markdown
### Changed

- **Breaking:** Renamed all slash commands from `/issue-*` to `/iflow-*` for consistency (#71). The dispatcher `/iflow` is now the namespace root. Skills renamed from `issueflow-issue-*` to `iflow-*`. Run `issue-flow update` to migrate existing projects; old files are automatically pruned.
- Renamed `/graphify` → `/iflow-graphify` for family consistency.
```

## Risk assessment

**High confidence areas:**
- Manifest updates in `templating.py` are straightforward
- Template file renames are mechanical
- Cross-reference updates are tedious but low-risk (grep-and-replace)

**Medium confidence areas:**
- Pruning logic in `init.py` — needs careful path handling to avoid deleting wrong files
- Test updates — many hardcoded names, easy to miss one

**Low risk:**
- Breaking existing users' workflows — this is a deliberate breaking change for v0.5.0, well-communicated

**Mitigation:**
- Thorough grep after implementation to catch lingering old names
- Run full test suite multiple times
- Test both fresh `init` and `update` scenarios manually
- Clear communication in HISTORY.md and release notes

## Summary

This is a comprehensive but straightforward rename across ~35 files. The core changes are in `templating.py` (manifests), physical template file renames, cross-reference updates throughout, test updates, and adding pruning logic. The migration strategy (prune on update) gives the cleanest UX. Estimated complexity: medium (tedious but not complex).

---

**Ready to implement?** This plan addresses all open questions from the issue and provides a complete checklist for execution.
