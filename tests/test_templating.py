"""Tests for issue_flow.templating."""

from __future__ import annotations

from pathlib import Path

from issue_flow.templating import (
    TEMPLATE_MANIFEST,
    render_template,
    resolve_output_path,
)


def test_all_templates_render_without_error() -> None:
    """Every template in the manifest should render with default context values."""
    context = {
        "issueflows_dir": ".issueflows",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
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
    # 8 commands + 1 rule + 1 doc + 9 skills = 19
    assert len(TEMPLATE_MANIFEST) == 19


def test_manifest_has_expected_commands_and_skills() -> None:
    """Every expected slash command and skill has a manifest entry."""
    template_names = {name for name, _ in TEMPLATE_MANIFEST}
    for command in (
        "iflow",
        "issue-init",
        "issue-plan",
        "issue-start",
        "issue-pause",
        "issue-close",
        "issue-cleanup",
        "issue-yolo",
    ):
        assert f"commands/{command}.md.j2" in template_names
    for skill in (
        "issueflow_iflow",
        "issueflow_issue_init",
        "issueflow_issue_plan",
        "issueflow_issue_start",
        "issueflow_issue_pause",
        "issueflow_issue_close",
        "issueflow_issue_cleanup",
        "issueflow_issue_yolo",
        "issueflow_version_bump",
    ):
        assert f"skills/{skill}/SKILL.md.j2" in template_names


def _default_context() -> dict[str, str]:
    return {
        "issueflows_dir": ".issueflows",
        "agent_dir": ".cursor",
        "docs_dir": "docs",
        "tools_folder": "00-tools",
        "current_issues_folder": "01-current-issues",
        "partly_solved_folder": "02-partly-solved-issues",
        "solved_folder": "03-solved-issues",
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
