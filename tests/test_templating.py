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
    assert len(TEMPLATE_MANIFEST) == 9
