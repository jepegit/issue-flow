"""Tests for issue_flow.init (the init command)."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from issue_flow import dependencies as deps_module
from issue_flow import init as init_module
from issue_flow.dependencies import REQUIRED_DEPENDENCIES
from issue_flow.init import run_init


def test_init_creates_dotenv_with_commented_keys(tmp_path: Path) -> None:
    """init should create .env with commented ISSUEFLOW_* defaults when absent."""
    run_init(tmp_path)

    env_file = tmp_path / ".env"
    assert env_file.is_file()
    text = env_file.read_text(encoding="utf-8")
    assert "# ISSUEFLOW_DIR=.issueflows" in text
    assert "# ISSUEFLOW_AGENT_DIR=.cursor" in text
    assert "# ISSUEFLOW_DOCS_DIR=docs" in text
    assert "# ISSUEFLOW_HISTORY_FILE=HISTORY.md" in text


def test_init_second_run_skips_dotenv_when_keys_documented(tmp_path: Path) -> None:
    """Re-running init should not append duplicate ISSUEFLOW_* hints."""
    run_init(tmp_path)
    first = (tmp_path / ".env").read_text(encoding="utf-8")

    run_init(tmp_path)
    second = (tmp_path / ".env").read_text(encoding="utf-8")

    assert first == second


def test_init_appends_missing_dotenv_keys(tmp_path: Path) -> None:
    """If .env exists without ISSUEFLOW_* lines, init should append commented hints."""
    (tmp_path / ".env").write_text("OTHER=1\n", encoding="utf-8")

    run_init(tmp_path)

    text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert text.startswith("OTHER=1\n")
    assert "issue-flow: optional environment" in text
    assert "# ISSUEFLOW_DIR=.issueflows" in text
    assert "# ISSUEFLOW_AGENT_DIR=.cursor" in text
    assert "# ISSUEFLOW_DOCS_DIR=docs" in text
    assert "# ISSUEFLOW_HISTORY_FILE=HISTORY.md" in text


def test_init_force_does_not_wipe_custom_dotenv(tmp_path: Path) -> None:
    """init --force must not replace an existing .env wholesale."""
    run_init(tmp_path)
    env_file = tmp_path / ".env"
    custom = (
        "MY_SECRET=keep-me\n"
        "# ISSUEFLOW_DIR=.issueflows\n"
        "# ISSUEFLOW_AGENT_DIR=.cursor\n"
        "# ISSUEFLOW_DOCS_DIR=docs\n"
        "# ISSUEFLOW_HISTORY_FILE=HISTORY.md\n"
    )
    env_file.write_text(custom, encoding="utf-8")

    run_init(tmp_path, force=True)

    assert "MY_SECRET=keep-me" in env_file.read_text(encoding="utf-8")


def test_init_creates_directories(tmp_path: Path) -> None:
    """Running init should create .issueflows/ with all five subdirectories."""
    run_init(tmp_path)

    issueflows = tmp_path / ".issueflows"
    assert issueflows.is_dir()
    assert (issueflows / "00-tools").is_dir()
    assert (issueflows / "01-current-issues").is_dir()
    assert (issueflows / "02-partly-solved-issues").is_dir()
    assert (issueflows / "03-solved-issues").is_dir()
    assert (issueflows / "04-designs-and-guides").is_dir()


def test_init_creates_gitkeep_files(tmp_path: Path) -> None:
    """Each .issueflows/ subdirectory should contain a .gitkeep file."""
    run_init(tmp_path)

    issueflows = tmp_path / ".issueflows"
    for subdir in [
        "00-tools",
        "01-current-issues",
        "02-partly-solved-issues",
        "03-solved-issues",
        "04-designs-and-guides",
    ]:
        gitkeep = issueflows / subdir / ".gitkeep"
        assert gitkeep.is_file(), f"{subdir}/.gitkeep should exist"


def test_init_creates_cursor_commands(tmp_path: Path) -> None:
    """Running init should create all three slash-command files."""
    run_init(tmp_path)

    commands_dir = tmp_path / ".cursor" / "commands"
    assert (commands_dir / "issue-init.md").is_file()
    assert (commands_dir / "issue-start.md").is_file()
    assert (commands_dir / "issue-close.md").is_file()


def test_init_creates_cursor_skills(tmp_path: Path) -> None:
    """Running init should create bundled Agent Skills under .cursor/skills/."""
    run_init(tmp_path)

    skills = tmp_path / ".cursor" / "skills"
    for name in (
        "issueflow-issue-init",
        "issueflow-issue-start",
        "issueflow-issue-close",
        "issueflow-version-bump",
        "issueflow-history-update",
    ):
        skill_file = skills / name / "SKILL.md"
        assert skill_file.is_file(), f"expected {skill_file}"
        text = skill_file.read_text(encoding="utf-8")
        assert text.startswith("---")
        assert f"name: {name}" in text
        assert "disable-model-invocation: true" in text


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


def test_init_issue_close_documents_version_bump(tmp_path: Path) -> None:
    """issue-close.md should describe optional uv semver bump before commit/PR."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "commands" / "issue-close.md").read_text(
        encoding="utf-8"
    )
    assert "uv version --bump" in content
    assert "issueflow-version-bump" in content


def test_init_issue_close_documents_history_update_step(tmp_path: Path) -> None:
    """issue-close.md should describe the HISTORY.md update step and opt-out token."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "commands" / "issue-close.md").read_text(
        encoding="utf-8"
    )
    assert "HISTORY.md" in content
    assert "issueflow-history-update" in content
    assert "[Unreleased]" in content
    assert "nohistory" in content


def test_init_issue_close_documents_uncommitted_and_branch_reminder(
    tmp_path: Path,
) -> None:
    """issue-close.md should flag unrelated uncommitted changes and warn about the issue branch after PR."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "commands" / "issue-close.md").read_text(
        encoding="utf-8"
    )
    assert "git status" in content
    assert "not relevant" in content
    assert "issue branch" in content


def test_init_rule_documents_designs_folder(tmp_path: Path) -> None:
    """The generated rule file should mention the designs-and-guides folder."""
    run_init(tmp_path)
    rule = (tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc").read_text(
        encoding="utf-8"
    )
    assert "04-designs-and-guides" in rule
    assert "Designs and guides" in rule


def test_init_commands_reference_designs_folder(tmp_path: Path) -> None:
    """/issue-plan, /issue-start, and /issue-close should reference the designs folder."""
    run_init(tmp_path)
    commands_dir = tmp_path / ".cursor" / "commands"
    for filename in ("issue-plan.md", "issue-start.md", "issue-close.md"):
        content = (commands_dir / filename).read_text(encoding="utf-8")
        assert "04-designs-and-guides" in content, (
            f"{filename} should reference the designs-and-guides folder"
        )


def test_init_issue_init_documents_branch_inference(tmp_path: Path) -> None:
    """issue-init.md should describe resolving an issue from the current branch when no args."""
    run_init(tmp_path)
    content = (tmp_path / ".cursor" / "commands" / "issue-init.md").read_text(
        encoding="utf-8"
    )
    assert "git branch --show-current" in content
    assert "You have not provided an issue reference" in content
    assert "issue-style branch" in content


def test_init_proceeds_silently_when_all_dependencies_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """With all deps present the check should not prompt or abort."""
    monkeypatch.setattr(init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES[:0]))

    def fail_confirm(*_a: object, **_kw: object) -> bool:
        raise AssertionError("typer.confirm should not be called when all deps present")

    monkeypatch.setattr(typer, "confirm", fail_confirm)

    run_init(tmp_path)

    assert (tmp_path / ".cursor" / "commands" / "issue-init.md").is_file()


def test_init_continues_when_skip_dep_check_is_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``skip_dep_check=True`` must bypass the prompt even if deps are missing."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES)
    )

    def fail_confirm(*_a: object, **_kw: object) -> bool:
        raise AssertionError("typer.confirm must not run when --skip-dep-check is set")

    monkeypatch.setattr(typer, "confirm", fail_confirm)

    run_init(tmp_path, skip_dep_check=True)

    assert (tmp_path / ".cursor" / "commands" / "issue-init.md").is_file()


def test_init_continues_in_non_tty_when_deps_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-interactive stdin (CI) must auto-skip the prompt."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES)
    )
    monkeypatch.setattr(deps_module.sys.stdin, "isatty", lambda: False)

    def fail_confirm(*_a: object, **_kw: object) -> bool:
        raise AssertionError("typer.confirm must not run on non-TTY stdin")

    monkeypatch.setattr(typer, "confirm", fail_confirm)

    run_init(tmp_path)

    assert (tmp_path / ".cursor" / "commands" / "issue-init.md").is_file()


def test_init_aborts_cleanly_when_user_declines_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A decline at the prompt must raise typer.Exit and leave no scaffold behind."""
    monkeypatch.setattr(
        init_module, "check_dependencies", lambda: list(REQUIRED_DEPENDENCIES)
    )
    monkeypatch.setattr(deps_module.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(typer, "confirm", lambda *_a, **_kw: False)

    with pytest.raises(typer.Exit) as exc_info:
        run_init(tmp_path)

    assert exc_info.value.exit_code == 1
    assert not (tmp_path / ".cursor").exists()
    assert not (tmp_path / ".issueflows").exists()


def test_init_detects_project_name(tmp_path: Path) -> None:
    """If a pyproject.toml exists, its name should appear in the rule file."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    run_init(tmp_path)

    rule = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    content = rule.read_text(encoding="utf-8")
    assert "test-project" in content
