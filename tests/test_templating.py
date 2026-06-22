"""Tests for issue_flow.templating."""

from __future__ import annotations

from pathlib import Path

from issue_flow.editors import EDITORS, get_profile
from issue_flow.templating import (
    TEMPLATE_MANIFEST,
    build_manifest,
    render_template,
    resolve_output_path,
)


def test_all_templates_render_without_error() -> None:
    """Every template in the manifest should render with default context values."""
    context = {
        "issueflows_dir": ".issueflows",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "history_file": "HISTORY.md",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
        "project_name": "test-project",
    }
    for template_name, _ in TEMPLATE_MANIFEST:
        result = render_template(template_name, context)
        assert isinstance(result, str)
        assert len(result) > 0, f"Template {template_name} rendered empty"


def test_template_substitution() -> None:
    """Template variables should be replaced in the rendered output."""
    context = {
        "issueflows_dir": "CUSTOM_DIR",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "history_file": "HISTORY.md",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
        "project_name": "my-project",
    }
    rendered = render_template("commands/issue-init.md.j2", context)
    assert "CUSTOM_DIR/01-current-issues" in rendered
    assert "{{ issueflows_dir }}" not in rendered


def test_resolve_output_path() -> None:
    context = {"agent_dir": ".cursor", "docs_dir": "docs"}
    path = resolve_output_path("{agent_dir}/commands/issue-init.md", context)
    assert path == Path(".cursor/commands/issue-init.md")


def test_manifest_entry_count() -> None:
    # 12 commands + 1 rule + 1 doc + 15 skills = 29
    assert len(TEMPLATE_MANIFEST) == 29


def _resolved_paths(profile_id: str) -> set[str]:
    """All resolved output paths for a profile, as forward-slash strings."""
    profile = get_profile(profile_id)
    context = {
        "agent_dir": profile.agent_dir,
        "commands_dir": profile.commands_dir or "commands",
        "docs_dir": "docs",
    }
    return {
        resolve_output_path(path_template, context).as_posix()
        for _, path_template in build_manifest(profile)
    }


def test_build_manifest_cursor_matches_default() -> None:
    """The default TEMPLATE_MANIFEST is the cursor profile manifest."""
    assert build_manifest(EDITORS["cursor"]) == TEMPLATE_MANIFEST
    assert len(build_manifest(EDITORS["cursor"])) == 29


def test_build_manifest_codex_has_skills_and_docs_but_no_commands() -> None:
    """Codex: skills (15) + docs (1), no slash commands and no rules extra."""
    manifest = build_manifest(get_profile("codex"))
    template_names = [name for name, _ in manifest]
    assert not any(name.startswith("commands/") for name in template_names)
    assert sum(name.startswith("skills/") for name in template_names) == 15
    assert "docs/issue-workflow.md.j2" in template_names
    # No .mdc / CLAUDE.md rules extra for Codex.
    assert not any(name.startswith("rules/") for name in template_names)
    assert len(manifest) == 16


def test_build_manifest_opencode_uses_singular_command_dir() -> None:
    paths = _resolved_paths("opencode")
    assert ".opencode/command/issue-init.md" in paths
    assert ".opencode/skills/issueflow-issue-init/SKILL.md" in paths
    # opencode has no editor-specific rules file (AGENTS.md is handled by init).
    assert not any(p.endswith(".mdc") for p in paths)
    assert "CLAUDE.md" not in paths


def test_build_manifest_claude_emits_claude_md_and_commands() -> None:
    manifest = build_manifest(get_profile("claude"))
    assert ("rules/CLAUDE.md.j2", "CLAUDE.md") in manifest
    paths = _resolved_paths("claude")
    assert ".claude/commands/issue-init.md" in paths
    assert "CLAUDE.md" in paths


def test_build_manifest_no_cursor_leakage_in_non_cursor_outputs() -> None:
    """Non-cursor editors must not write under .cursor/ or mention "Cursor"."""
    for editor_id in ("claude", "opencode", "codex"):
        profile = get_profile(editor_id)
        context = {
            "issueflows_dir": ".issueflows",
            "agent_dir": profile.agent_dir,
            "docs_dir": "docs",
            "history_file": "HISTORY.md",
            "tools_folder": "00-tools",
            "current_issues_folder": "01-current-issues",
            "partly_solved_folder": "02-partly-solved-issues",
            "solved_folder": "03-solved-issues",
            "designs_folder": "04-designs-and-guides",
            "project_name": "test-project",
            "editor": profile.id,
            "editor_name": profile.name,
            "commands_dir": profile.commands_dir or "commands",
            "graphify_installer": profile.graphify_installer or "",
        }
        manifest = build_manifest(profile) + [("rules/AGENTS.md.j2", "AGENTS.md")]
        for template_name, path_template in manifest:
            resolved = resolve_output_path(path_template, context).as_posix()
            assert ".cursor" not in resolved, f"{editor_id}: {resolved}"
            rendered = render_template(template_name, context)
            assert "Cursor" not in rendered, (
                f"{editor_id} output {template_name} leaks literal 'Cursor'"
            )


def test_manifest_has_expected_commands_and_skills() -> None:
    """Every expected slash command and skill has a manifest entry."""
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    for command in (
        "iflow",
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
    ):
        assert f"commands/{command}.md.j2" in template_names
    for skill in (
        "issueflow_iflow",
        "issueflow_issue_pick",
        "issueflow_issue_init",
        "issueflow_issue_comments",
        "issueflow_issue_plan",
        "issueflow_issue_start",
        "issueflow_issue_pause",
        "issueflow_issue_close",
        "issueflow_issue_cleanup",
        "issueflow_issue_yolo",
        "issueflow_issue_fix",
        "issueflow_issue_status",
        "issueflow_version_bump",
        "issueflow_history_update",
        "issueflow_graphify",
    ):
        assert f"skills/{skill}/SKILL.md.j2" in template_names


def _default_context() -> dict[str, str]:
    return {
        "issueflows_dir": ".issueflows",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "history_file": "HISTORY.md",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
        "designs_folder": "04-designs-and-guides",
        "project_name": "test-project",
    }


def test_issue_start_mentions_branch_and_sweep_preflight() -> None:
    """The /issue-start command must include the new preflight and sweep steps."""
    rendered = render_template("commands/issue-start.md.j2", _default_context())
    assert "Branch status preflight" in rendered
    assert "Sweep stale current issues" in rendered
    assert "git fetch --prune" in rendered


def test_issue_close_delegates_post_merge_cleanup_to_issue_cleanup() -> None:
    """/issue-close no longer deletes branches; it points at /issue-cleanup instead."""
    rendered = render_template("commands/issue-close.md.j2", _default_context())
    assert "/issue-cleanup" in rendered
    assert "git pull --ff-only" in rendered
    # The destructive branch delete lives in /issue-cleanup now, not /issue-close.
    assert "git branch -d" not in rendered


def test_issue_cleanup_describes_post_merge_branch_cleanup() -> None:
    """The /issue-cleanup command owns the post-merge branch cleanup logic."""
    rendered = render_template("commands/issue-cleanup.md.j2", _default_context())
    assert "git branch -d" in rendered
    assert "git pull --ff-only" in rendered
    assert "gh pr view" in rendered
    # Never -D automatically.
    assert "-D" not in rendered or "Never use `-D`" in rendered or "Never `-D`" in rendered


def test_issue_start_requires_or_offers_plan() -> None:
    """/issue-start should read the plan file and offer to run /issue-plan when missing."""
    rendered = render_template("commands/issue-start.md.j2", _default_context())
    assert "issue<N>_plan.md" in rendered
    assert "/issue-plan" in rendered


def test_issue_plan_writes_plan_file_and_stops_for_confirmation() -> None:
    """/issue-plan must produce a plan file and require confirmation."""
    rendered = render_template("commands/issue-plan.md.j2", _default_context())
    assert "issue<N>_plan.md" in rendered
    assert "Goal" in rendered
    assert "Approach" in rendered
    assert "Confirm" in rendered or "confirmation" in rendered.lower()
    assert "1.75" in rendered
    assert "Prior-art discovery" in rendered
    assert "GRAPH_REPORT.md" in rendered
    assert "### Prior art" in rendered


def test_issue_plan_includes_prior_art_discovery() -> None:
    """/issue-plan must document graceful graphify + grep prior-art checklist."""
    rendered = render_template("commands/issue-plan.md.j2", _default_context())
    assert "Prior-art discovery" in rendered
    assert "God Nodes" in rendered
    assert "None found (grep + graph checked)" in rendered
    assert "Open questions" in rendered
    skill = render_template("skills/issueflow_issue_plan/SKILL.md.j2", _default_context())
    assert "Prior-art discovery" in skill or "Prior art" in skill
    assert "### Prior art" in skill


def test_issue_start_reads_prior_art_from_plan() -> None:
    """/issue-start should remind the agent to read ### Prior art from the plan."""
    rendered = render_template("commands/issue-start.md.j2", _default_context())
    assert "### Prior art" in rendered
    skill = render_template("skills/issueflow_issue_start/SKILL.md.j2", _default_context())
    assert "### Prior art" in skill


def test_issue_pause_moves_to_partly_solved() -> None:
    """/issue-pause moves the issue group to the partly-solved folder."""
    rendered = render_template("commands/issue-pause.md.j2", _default_context())
    assert "02-partly-solved-issues" in rendered
    assert "Remaining work" in rendered
    assert "- [ ] Done" in rendered


def test_issue_yolo_has_safeguards() -> None:
    """/issue-yolo must advertise the up-front safeguards before chaining."""
    rendered = render_template("commands/issue-yolo.md.j2", _default_context())
    assert "uv run pytest" in rendered
    assert "default branch" in rendered.lower()
    # Must not chain cleanup automatically.
    assert "/issue-cleanup" in rendered


def test_issue_fix_describes_interactive_session() -> None:
    """/issue-fix must describe the off-path interactive iterative-fix session."""
    rendered = render_template("commands/issue-fix.md.j2", _default_context())
    # Off-path and explicitly not driven by /iflow during a session.
    assert "off-path" in rendered.lower()
    assert "/iflow" in rendered
    # Always creates a GitHub issue via gh; GitLab is out of scope.
    assert "gh issue create" in rendered
    assert "GitLab is not supported" in rendered
    # The fix loop records each fix in the status file's log section.
    assert "Iterative fixes log" in rendered
    assert "issue<N>_status.md" in rendered
    # Branch-from-current-vs-default choice and delegation to init/close.
    assert "/issue-init" in rendered
    assert "/issue-close" in rendered
    # Keeps the unchecked Done checkbox during the session.
    assert "- [ ] Done" in rendered


def test_issue_fix_skill_mirrors_command() -> None:
    """The issue-fix skill must carry the same session flow and frontmatter."""
    rendered = render_template(
        "skills/issueflow_issue_fix/SKILL.md.j2", _default_context()
    )
    assert "name: issueflow-issue-fix" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "gh issue create" in rendered
    assert "Iterative fixes log" in rendered
    assert "/issue-init" in rendered
    assert "/issue-close" in rendered


def test_iflow_lists_issue_fix_as_off_path() -> None:
    """/iflow and its skill must list /issue-fix among the explicit-only commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/issueflow_iflow/SKILL.md.j2", _default_context())
    assert "/issue-fix" in cmd
    assert "/issue-fix" in skill


def test_iflow_describes_state_machine() -> None:
    """/iflow must describe the four-state dispatch and name its downstream targets."""
    rendered = render_template("commands/iflow.md.j2", _default_context())
    # Dispatches into all four linear-flow commands.
    for target in (
        "/issue-init",
        "/issue-plan",
        "/issue-start",
        "/issue-close",
    ):
        assert target in rendered, f"/iflow must mention {target}"
    # State keywords from the dispatch table.
    assert "_original.md" in rendered
    assert "_plan.md" in rendered
    assert "- [x] Done" in rendered
    # Off-path commands are explicitly not auto-dispatched.
    assert "/issue-pause" in rendered
    assert "/issue-cleanup" in rendered
    assert "/issue-yolo" in rendered


def test_iflow_treats_branch_derived_n_as_authoritative() -> None:
    """/iflow's step 0 must treat a branch-derived N as authoritative.

    The branch-derived N should win even when `issue<N>_*` files don't exist
    yet, or when unrelated groups sit in 01-current-issues. It should also
    trigger the archived-issue guard warning when the group lives in
    02-partly-solved or 03-solved.
    """
    rendered = render_template("commands/iflow.md.j2", _default_context())
    assert "authoritative" in rendered.lower()
    # Both archive folders are consulted for the archived-issue guard warning.
    assert "02-partly-solved-issues" in rendered
    assert "03-solved-issues" in rendered
    assert "archived-issue guard" in rendered.lower()


def test_issue_pick_documents_three_phases_and_fix_shortcut() -> None:
    """/issue-pick must describe its three phases, ranking inputs, and the `fix` shortcut."""
    rendered = render_template("commands/issue-pick.md.j2", _default_context())
    # Three phases.
    assert "Phase 1" in rendered
    assert "Phase 2" in rendered
    assert "Phase 3" in rendered
    # Parked work is the primary candidate source, GitHub the fallback.
    assert "02-partly-solved-issues" in rendered
    assert "gh issue list" in rendered
    # Relevance ranking combines milestone + labels + topical similarity.
    assert "Milestone" in rendered or "milestone" in rendered
    assert "Labels" in rendered or "label" in rendered
    # `fix` shortcut creates a new issue every time.
    assert "fix" in rendered
    assert "gh issue create" in rendered
    # Delegates capture to /issue-init and hands off to /issue-plan.
    assert "/issue-init" in rendered
    assert "/issue-plan" in rendered
    # Off-path: not auto-dispatched by /iflow.
    assert "off-path" in rendered.lower()
    # Phase B (auto sub-issue creation) is explicitly out of scope.
    assert "Phase B" in rendered


def test_issue_pick_skill_mirrors_command() -> None:
    """The issue-pick skill must carry the same front-door flow and frontmatter."""
    rendered = render_template(
        "skills/issueflow_issue_pick/SKILL.md.j2", _default_context()
    )
    assert "name: issueflow-issue-pick" in rendered
    assert "disable-model-invocation: true" in rendered
    assert "Phase 1" in rendered
    assert "Phase 2" in rendered
    assert "Phase 3" in rendered
    assert "/issue-init" in rendered
    assert "/issue-plan" in rendered


def test_iflow_does_not_auto_dispatch_issue_pick() -> None:
    """/iflow must list /issue-pick among the explicit-only, never-auto-dispatched commands."""
    cmd = render_template("commands/iflow.md.j2", _default_context())
    skill = render_template("skills/issueflow_iflow/SKILL.md.j2", _default_context())
    assert "/issue-pick" in cmd
    assert "/issue-pick" in skill


def test_issue_init_mentions_branch_preflight_and_archive_guard() -> None:
    """The /issue-init command must include the preflight and archived-issue guard."""
    rendered = render_template("commands/issue-init.md.j2", _default_context())
    assert "Branch status preflight" in rendered
    assert "Archived-issue guard" in rendered or "archived" in rendered.lower()


def test_issueflow_rules_has_branch_hygiene_section() -> None:
    """The workspace rules must describe branch and folder hygiene expectations."""
    rendered = render_template("rules/issueflow-rules.mdc.j2", _default_context())
    assert "Branch hygiene" in rendered
    assert "git branch -d" in rendered
    assert "Folder hygiene" in rendered


def test_rules_body_defers_to_project_toolchain_and_covers_conda() -> None:
    """Regression for issue #58: the shared rules body must defer to the
    project's existing toolchain and cover conda, not hard-mandate uv."""
    # The body is included by all three rules outputs; assert on each so none drift.
    for template_name in (
        "rules/issueflow-rules.mdc.j2",
        "rules/AGENTS.md.j2",
        "rules/CLAUDE.md.j2",
    ):
        rendered = render_template(template_name, _default_context())
        lowered = rendered.lower()
        # Defers to whatever the project already documents.
        assert "respect the project's existing toolchain" in lowered
        # conda is explicitly covered, including pytest inside the activated env.
        assert "conda" in lowered
        assert "conda activate" in rendered
        assert "conda run -n" in rendered
        # uv stays the documented default/example…
        assert "uv run" in rendered
        # …but the old hard mandate is gone.
        assert "Use `uv` exclusively" not in rendered
        assert "uv exclusively" not in lowered


def test_issue_close_describes_history_update_step() -> None:
    """/issue-close must describe the HISTORY.md update step and its input tokens."""
    rendered = render_template("commands/issue-close.md.j2", _default_context())
    assert "HISTORY.md" in rendered
    assert "[Unreleased]" in rendered
    assert "issueflow-history-update" in rendered
    # Opt-out token is documented.
    assert "nohistory" in rendered
    # Override token for the bullet summary is documented.
    assert 'log "..."' in rendered or "log " in rendered


def test_history_update_skill_documents_both_modes() -> None:
    """The history-update skill must describe append-and-promote, plus the missing-file fallback."""
    rendered = render_template(
        "skills/issueflow_history_update/SKILL.md.j2", _default_context()
    )
    assert "HISTORY.md" in rendered
    assert "[Unreleased]" in rendered
    # Append mode (no bump) and promote mode (with bump) are both described.
    assert "append" in rendered.lower()
    assert "promote" in rendered.lower()
    # Gracefully skip when the file is missing; never auto-create.
    assert "skipping changelog" in rendered.lower() or "skip" in rendered.lower()
    assert "Never create" in rendered or "never create" in rendered.lower()


def test_history_update_skill_respects_history_file_override() -> None:
    """The history-update skill should reference {{ history_file }} so custom filenames work."""
    context = _default_context()
    context["history_file"] = "CHANGELOG.md"
    rendered = render_template(
        "skills/issueflow_history_update/SKILL.md.j2", context
    )
    assert "CHANGELOG.md" in rendered
    # No leftover Jinja placeholder.
    assert "{{ history_file }}" not in rendered


def test_issue_yolo_forwards_history_tokens() -> None:
    """/issue-yolo must forward the new history-related tokens to /issue-close."""
    rendered = render_template("commands/issue-yolo.md.j2", _default_context())
    assert "nohistory" in rendered
    assert "log " in rendered  # `log "..."` bullet-summary override


def test_issue_init_fetches_and_triages_comments() -> None:
    """/issue-init must fetch comments and call the comments-triage skill."""
    rendered = render_template("commands/issue-init.md.j2", _default_context())
    # gh fetch now asks for the comments field too.
    assert "title,body,url,number,comments" in rendered
    # The curated section header appears in the file-content template.
    assert "## Comments (curated summary)" in rendered
    # The triage step exists and delegates to the new skill.
    assert "Triage comments" in rendered
    assert "issueflow-issue-comments" in rendered
    # The three triage buckets are named.
    assert "Additional tasks" in rendered
    assert "Clarifications" in rendered
    assert "Superseded" in rendered
    # The body contract: preserve the fetched body text faithfully, but the
    # "Agent efficiency" guidance (issue #9) says not to obsess over byte-exactness.
    assert "Agent efficiency" in rendered
    assert "Preserve the issue **body** text exactly as returned by GitHub" in rendered


def test_issue_init_documents_agent_efficiency() -> None:
    """Regression guard for issue #9: the Agent efficiency guidance must live in the template.

    It was originally added only to the generated `.cursor/commands/issue-init.md` and got
    wiped by a later regeneration; it now belongs in the source template so it survives.
    """
    rendered = render_template("commands/issue-init.md.j2", _default_context())
    assert "## Agent efficiency" in rendered
    assert "trailing newlines" in rendered
    assert "CRLF" in rendered
    # The reconciled body contract no longer demands literal byte-for-byte equality.
    assert "byte-for-byte" not in rendered
    # The mirror skill should not re-introduce the stricter "byte-for-byte" wording.
    skill = render_template(
        "skills/issueflow_issue_init/SKILL.md.j2", _default_context()
    )
    assert "byte-for-byte" not in skill


def test_issue_init_skill_delegates_to_comments_skill() -> None:
    """The issue-init skill must fetch comments and point at the comments skill."""
    rendered = render_template(
        "skills/issueflow_issue_init/SKILL.md.j2", _default_context()
    )
    assert "title,body,url,number,comments" in rendered
    assert "issueflow-issue-comments" in rendered
    assert "## Comments (curated summary)" in rendered


def test_issue_comments_skill_documents_triage_rules() -> None:
    """The new issueflow-issue-comments skill must describe triage rules and buckets."""
    rendered = render_template(
        "skills/issueflow_issue_comments/SKILL.md.j2", _default_context()
    )
    # Frontmatter identity.
    assert "name: issueflow-issue-comments" in rendered
    assert "disable-model-invocation: true" in rendered
    # Chronological precedence (later wins) is called out.
    lowered = rendered.lower()
    assert "chronological" in lowered
    assert "later" in lowered
    # All three buckets are named.
    assert "Additional tasks" in rendered
    assert "Clarifications" in rendered
    assert "Superseded" in rendered
    # The output contract header matches exactly what /issue-init expects.
    assert "## Comments (curated summary)" in rendered
    # Noise-filtering guidance exists.
    assert "bot" in lowered
    # Zero-comment edge case is handled.
    assert "zero comments" in lowered or "skip the whole section" in lowered
