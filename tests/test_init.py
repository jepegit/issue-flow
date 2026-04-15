"""Tests for issue_flow.init (the init command)."""

from __future__ import annotations

from pathlib import Path

from issue_flow.init import run_init


def test_init_creates_directories(tmp_path: Path) -> None:
    """Running init should create .issueflows/ with all four subdirectories."""
    run_init(tmp_path)

    issueflows = tmp_path / ".issueflows"
    assert issueflows.is_dir()
    assert (issueflows / "00-tools").is_dir()
    assert (issueflows / "01-current-issues").is_dir()
    assert (issueflows / "02-partly-solved-issues").is_dir()
    assert (issueflows / "03-solved-issues").is_dir()


def test_init_creates_gitkeep_files(tmp_path: Path) -> None:
    """Each .issueflows/ subdirectory should contain a .gitkeep file."""
    run_init(tmp_path)

    issueflows = tmp_path / ".issueflows"
    for subdir in ["00-tools", "01-current-issues", "02-partly-solved-issues", "03-solved-issues"]:
        gitkeep = issueflows / subdir / ".gitkeep"
        assert gitkeep.is_file(), f"{subdir}/.gitkeep should exist"


def test_init_creates_cursor_commands(tmp_path: Path) -> None:
    """Running init should create all three slash-command files."""
    run_init(tmp_path)

    commands_dir = tmp_path / ".cursor" / "commands"
    assert (commands_dir / "issue-init.md").is_file()
    assert (commands_dir / "issue-start.md").is_file()
    assert (commands_dir / "issue-close.md").is_file()


def test_init_creates_cursor_rule(tmp_path: Path) -> None:
    run_init(tmp_path)
    rule = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    assert rule.is_file()
    content = rule.read_text(encoding="utf-8")
    assert "alwaysApply: true" in content
    assert ".issueflows" in content


def test_init_creates_docs(tmp_path: Path) -> None:
    run_init(tmp_path)
    doc = tmp_path / "docs" / "cursor-issue-workflow.md"
    assert doc.is_file()
    content = doc.read_text(encoding="utf-8")
    assert "/issue-init" in content
    assert ".issueflows" in content


def test_init_idempotent_skips_existing(tmp_path: Path) -> None:
    """Running init twice should skip files that already exist (no overwrite)."""
    run_init(tmp_path)

    # Tamper with a file so we can verify it was NOT overwritten
    rule_file = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    rule_file.write_text("custom content", encoding="utf-8")

    run_init(tmp_path)

    assert rule_file.read_text(encoding="utf-8") == "custom content"


def test_init_force_overwrites(tmp_path: Path) -> None:
    """Running init with force=True should overwrite existing files."""
    run_init(tmp_path)

    rule_file = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    rule_file.write_text("custom content", encoding="utf-8")

    run_init(tmp_path, force=True)

    content = rule_file.read_text(encoding="utf-8")
    assert content != "custom content"
    assert "alwaysApply: true" in content


def test_init_templates_reference_issueflows_dir(tmp_path: Path) -> None:
    """All generated command files should reference .issueflows/ paths."""
    run_init(tmp_path)

    commands_dir = tmp_path / ".cursor" / "commands"
    for filename in ["issue-init.md", "issue-start.md", "issue-close.md"]:
        content = (commands_dir / filename).read_text(encoding="utf-8")
        assert ".issueflows/" in content, f"{filename} should reference .issueflows/"


def test_init_issue_init_documents_branch_inference(tmp_path: Path) -> None:
    """issue-init.md should describe resolving an issue from the current branch when no args."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "commands" / "issue-init.md").read_text(encoding="utf-8")
    assert "git branch --show-current" in content
    assert "You have not provided an issue reference" in content
    assert "issue-style branch" in content


def test_init_detects_project_name(tmp_path: Path) -> None:
    """If a pyproject.toml exists, its name should appear in the rule file."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    run_init(tmp_path)

    rule = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    content = rule.read_text(encoding="utf-8")
    assert "test-project" in content
