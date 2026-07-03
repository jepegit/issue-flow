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

    skill = tmp_path / ".cursor" / "skills" / "iflow-init" / "SKILL.md"
    skill.write_text("custom skill", encoding="utf-8")

    run_update(tmp_path)

    content = skill.read_text(encoding="utf-8")
    assert content != "custom skill"
    assert "name: iflow-init" in content


def test_update_prunes_generated_cursor_commands_but_keeps_user_commands(
    tmp_path: Path,
) -> None:
    """Cursor migration removes known generated command files only."""
    run_init(tmp_path)
    commands_dir = tmp_path / ".cursor" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "iflow-init.md").write_text("generated", encoding="utf-8")
    (commands_dir / "iflow.md").write_text("generated", encoding="utf-8")
    (commands_dir / "my-command.md").write_text("user command", encoding="utf-8")

    run_update(tmp_path)

    assert not (commands_dir / "iflow-init.md").exists()
    assert not (commands_dir / "iflow.md").exists()
    assert (commands_dir / "my-command.md").read_text(
        encoding="utf-8"
    ) == "user command"


def test_update_prunes_empty_cursor_commands_dir(tmp_path: Path) -> None:
    """If only generated commands existed, update removes the old command dir."""
    run_init(tmp_path)
    commands_dir = tmp_path / ".cursor" / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "iflow-init.md").write_text("generated", encoding="utf-8")

    run_update(tmp_path)

    assert not commands_dir.exists()


def test_update_prunes_old_iflow_iflow_skill_folder(tmp_path: Path) -> None:
    """The old dispatcher skill folder is removed after the skill is renamed."""
    run_init(tmp_path)
    old_skill = tmp_path / ".cursor" / "skills" / "iflow-iflow"
    old_skill.mkdir(parents=True)
    (old_skill / "SKILL.md").write_text("old dispatcher", encoding="utf-8")

    run_update(tmp_path)

    assert not old_skill.exists()
    assert (tmp_path / ".cursor" / "skills" / "iflow" / "SKILL.md").is_file()


def test_update_recreates_removed_subdir(tmp_path: Path) -> None:
    """If an issueflows subdir was removed, update should recreate it."""
    run_init(tmp_path)

    removed = tmp_path / ".issueflows" / "00-tools"
    shutil.rmtree(removed)
    assert not removed.exists()

    run_update(tmp_path)

    assert removed.is_dir()
    assert (removed / ".gitkeep").is_file()


def test_update_preserves_designs_folder_contents(tmp_path: Path) -> None:
    """update must not touch user content inside 04-designs-and-guides/."""
    run_init(tmp_path)

    designs_dir = tmp_path / ".issueflows" / "04-designs-and-guides"
    design_doc = designs_dir / "logging-decision.md"
    body = "# Logging decision\n\nWe use structlog because X.\n"
    design_doc.write_text(body, encoding="utf-8")

    run_update(tmp_path)

    assert design_doc.read_text(encoding="utf-8") == body


def test_update_creates_project_brief_when_missing(tmp_path: Path) -> None:
    """update should recreate the starter project brief if it is missing."""
    run_init(tmp_path)
    brief = tmp_path / ".issueflows" / "04-designs-and-guides" / "this-project.md"
    brief.unlink()

    run_update(tmp_path)

    assert brief.is_file()
    text = brief.read_text(encoding="utf-8")
    assert "What this project is" in text
    assert "How to run / test" in text


def test_update_preserves_project_brief(tmp_path: Path) -> None:
    """update must not overwrite the user-owned project brief."""
    run_init(tmp_path)
    brief = tmp_path / ".issueflows" / "04-designs-and-guides" / "this-project.md"
    custom = "# Custom project brief\n\nDo not overwrite me.\n"
    brief.write_text(custom, encoding="utf-8")

    run_update(tmp_path)

    assert brief.read_text(encoding="utf-8") == custom


def test_update_creates_tools_readme_when_missing(tmp_path: Path) -> None:
    """update should recreate the 00-tools README if it is missing."""
    run_init(tmp_path)
    readme = tmp_path / ".issueflows" / "00-tools" / "README.md"
    readme.unlink()

    run_update(tmp_path)

    assert readme.is_file()
    assert "Tool index" in readme.read_text(encoding="utf-8")


def test_update_preserves_tools_readme(tmp_path: Path) -> None:
    """update must not overwrite the agent-grown tools index."""
    run_init(tmp_path)
    readme = tmp_path / ".issueflows" / "00-tools" / "README.md"
    custom = "# My toolbox\n\n| dedupe.py | drops dups | always |\n"
    readme.write_text(custom, encoding="utf-8")

    run_update(tmp_path)

    assert readme.read_text(encoding="utf-8") == custom


_AGENTS_BEGIN = "<!-- BEGIN issue-flow (managed: do not edit this block) -->"
_AGENTS_END = "<!-- END issue-flow (managed) -->"


def test_update_refreshes_agents_md_block_preserving_user_content(
    tmp_path: Path,
) -> None:
    """update refreshes the managed block in place but keeps user content."""
    run_init(tmp_path)

    agents = tmp_path / "AGENTS.md"

    # Simulate user content around the block + a tampered managed block body.
    preamble = "# My project\n\nKeep me.\n\n"
    tampered_block = f"{_AGENTS_BEGIN}\nOUTDATED\n{_AGENTS_END}\n"
    agents.write_text(preamble + tampered_block, encoding="utf-8")

    run_update(tmp_path)

    refreshed = agents.read_text(encoding="utf-8")
    assert refreshed.startswith("# My project")
    assert "Keep me." in refreshed
    assert "OUTDATED" not in refreshed
    assert "Issue-flow best practices" in refreshed
    assert refreshed.count(_AGENTS_BEGIN) == 1


def test_update_claude_editor_refreshes_claude_md(tmp_path: Path) -> None:
    """update --editor claude overwrites CLAUDE.md from the package."""
    run_init(tmp_path, editors=["claude"])

    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("custom", encoding="utf-8")

    run_update(tmp_path, editors=["claude"])

    content = claude_md.read_text(encoding="utf-8")
    assert content != "custom"
    assert "Issue-flow best practices" in content


def test_update_respects_persisted_simple_mode(tmp_path: Path) -> None:
    """update reads the persisted mode and keeps the surface narrow."""
    run_init(tmp_path, mode="simple")
    skills = tmp_path / ".cursor" / "skills"
    assert not (skills / "iflow-close").exists()

    run_update(tmp_path)

    # Excluded skills are not re-created by update.
    assert not (skills / "iflow-close").exists()
    assert not (skills / "iflow-yolo").exists()
    # Included skills are refreshed.
    assert (skills / "iflow-init" / "SKILL.md").is_file()


def test_update_default_mode_keeps_full_surface(tmp_path: Path) -> None:
    """With no persisted mode, update keeps the full standard scaffold."""
    run_init(tmp_path)
    run_update(tmp_path)

    skills = tmp_path / ".cursor" / "skills"
    assert (skills / "iflow-close" / "SKILL.md").is_file()
    assert (skills / "iflow-yolo" / "SKILL.md").is_file()


def test_update_prunes_after_external_mode_switch(tmp_path: Path) -> None:
    """Editing config.toml then running update prunes newly-excluded skills."""
    run_init(tmp_path)
    close = tmp_path / ".cursor" / "skills" / "iflow-close"
    assert close.is_dir()

    from issue_flow.modes import config_path, write_active_mode

    write_active_mode(config_path(tmp_path, ".issueflows"), "simple")
    run_update(tmp_path)

    assert not close.exists()


def test_update_recreates_removed_designs_folder(tmp_path: Path) -> None:
    """If 04-designs-and-guides/ was removed, update should recreate it."""
    run_init(tmp_path)

    removed = tmp_path / ".issueflows" / "04-designs-and-guides"
    shutil.rmtree(removed)
    assert not removed.exists()

    run_update(tmp_path)

    assert removed.is_dir()
    assert (removed / ".gitkeep").is_file()
