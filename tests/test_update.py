"""Tests for issue_flow.init.run_update."""

from __future__ import annotations

import shutil
from pathlib import Path

from issue_flow.init import run_init, run_update


def test_update_overwrites_scaffold(tmp_path: Path) -> None:
    """update should overwrite manifest files even when customized."""
    run_init(tmp_path)

    rule_file = tmp_path / ".cursor" / "rules" / "issueflow-rules.mdc"
    rule_file.write_text("custom content", encoding="utf-8")

    run_update(tmp_path)

    content = rule_file.read_text(encoding="utf-8")
    assert content != "custom content"
    assert "alwaysApply: true" in content


def test_update_preserves_issue_markdown(tmp_path: Path) -> None:
    """update must not modify issue markdown under .issueflows/."""
    run_init(tmp_path)

    issues_dir = tmp_path / ".issueflows" / "01-current-issues"
    issue_file = issues_dir / "issue99_original.md"
    distinctive = "USER_ISSUE_BODY_SHOULD_STAY_PUT\n"
    issue_file.write_text(distinctive, encoding="utf-8")

    run_update(tmp_path)

    assert issue_file.read_text(encoding="utf-8") == distinctive


def test_update_overwrites_skill_files(tmp_path: Path) -> None:
    """update should refresh packaged skills like other manifest outputs."""
    run_init(tmp_path)

    skill = tmp_path / ".cursor" / "skills" / "issueflow-issue-init" / "SKILL.md"
    skill.write_text("custom skill", encoding="utf-8")

    run_update(tmp_path)

    content = skill.read_text(encoding="utf-8")
    assert content != "custom skill"
    assert "name: issueflow-issue-init" in content


def test_update_recreates_removed_subdir(tmp_path: Path) -> None:
    """If an issueflows subdir was removed, update should recreate it."""
    run_init(tmp_path)

    removed = tmp_path / ".issueflows" / "00-tools"
    shutil.rmtree(removed)
    assert not removed.exists()

    run_update(tmp_path)

    assert removed.is_dir()
    assert (removed / ".gitkeep").is_file()
