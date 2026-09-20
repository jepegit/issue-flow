"""User-global materialize of ``both`` stems (caveman / grill-me / gh-ci / iflow-init)."""

from __future__ import annotations

from pathlib import Path

from issue_flow.init import run_init, run_update
from issue_flow.skill_ownership import user_global_stamp_key
from issue_flow.templating import BOTH_SKILL_STEMS, skill_output_name
from issue_flow.user_global import (
    editor_user_global_skills_root,
    user_global_skill_stamp_path,
)

_BOTH_OUTPUTS = tuple(skill_output_name(stem) for stem in BOTH_SKILL_STEMS)


def _assert_both_skills(root: Path) -> None:
    for output in _BOTH_OUTPUTS:
        skill = root / output / "SKILL.md"
        assert skill.is_file(), f"missing {skill}"
        text = skill.read_text(encoding="utf-8")
        assert "issue-flow-version:" in text
        assert f"name: {output}" in text


def test_editor_user_global_skills_root_is_per_editor() -> None:
    home = Path.home()
    assert editor_user_global_skills_root("cursor") == home / ".cursor" / "skills"
    assert editor_user_global_skills_root("claude") == home / ".claude" / "skills"
    assert editor_user_global_skills_root("codex") == home / ".agents" / "skills"
    assert editor_user_global_skills_root("unknown") is None
    cursor = editor_user_global_skills_root("cursor")
    claude = editor_user_global_skills_root("claude")
    assert cursor is not None and claude is not None
    assert cursor != claude


def test_opencode_global_skills_use_xdg_not_claude(monkeypatch, tmp_path: Path) -> None:
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    root = editor_user_global_skills_root("opencode")
    assert root == xdg / "opencode" / "skills"
    assert ".claude" not in root.as_posix()
    assert ".agents" not in root.as_posix()


def test_init_writes_both_stems_to_cursor_global_and_keeps_project(
    tmp_path: Path,
) -> None:
    run_init(tmp_path)

    project_skills = tmp_path / ".cursor" / "skills"
    _assert_both_skills(project_skills)

    global_root = editor_user_global_skills_root("cursor")
    assert global_root is not None
    _assert_both_skills(global_root)

    claude_global = editor_user_global_skills_root("claude")
    assert claude_global is not None
    assert not (claude_global / "caveman" / "SKILL.md").exists()

    stamps = user_global_skill_stamp_path()
    assert stamps.is_file()
    payload = stamps.read_text(encoding="utf-8")
    assert user_global_stamp_key("cursor", "caveman") in payload
    project_stamps = (
        tmp_path / ".issueflows" / "agent" / "skill-stamps.json"
    ).read_text(encoding="utf-8")
    assert "cursor/caveman" not in project_stamps
    assert ".cursor/skills/caveman" in project_stamps


def test_init_claude_writes_claude_global_not_cursor(tmp_path: Path) -> None:
    run_init(tmp_path, editors=["claude"])

    claude_global = editor_user_global_skills_root("claude")
    assert claude_global is not None
    _assert_both_skills(claude_global)
    _assert_both_skills(tmp_path / ".claude" / "skills")

    cursor_global = editor_user_global_skills_root("cursor")
    assert cursor_global is not None
    assert not (cursor_global / "caveman" / "SKILL.md").exists()


def test_init_opencode_writes_xdg_opencode_skills(tmp_path: Path) -> None:
    run_init(tmp_path, editors=["opencode"])
    root = editor_user_global_skills_root("opencode")
    assert root is not None
    _assert_both_skills(root)
    assert not (Path.home() / ".claude" / "skills" / "caveman" / "SKILL.md").exists()
    assert not (Path.home() / ".agents" / "skills" / "caveman" / "SKILL.md").exists()


def test_simple_mode_skips_global_both_stems(tmp_path: Path) -> None:
    run_init(tmp_path, mode="simple")
    global_root = editor_user_global_skills_root("cursor")
    assert global_root is not None
    assert not (global_root / "caveman" / "SKILL.md").exists()
    assert not (tmp_path / ".cursor" / "skills" / "caveman").exists()


def test_update_skips_foreign_global_without_force(tmp_path: Path) -> None:
    run_init(tmp_path)
    global_root = editor_user_global_skills_root("cursor")
    assert global_root is not None
    foreign = global_root / "caveman" / "SKILL.md"
    foreign.write_text("not ours\n", encoding="utf-8")

    run_update(tmp_path)

    assert foreign.read_text(encoding="utf-8") == "not ours\n"
    assert (tmp_path / ".cursor" / "skills" / "caveman" / "SKILL.md").is_file()


def test_update_force_overwrites_foreign_global(tmp_path: Path) -> None:
    run_init(tmp_path)
    global_root = editor_user_global_skills_root("cursor")
    assert global_root is not None
    foreign = global_root / "caveman" / "SKILL.md"
    foreign.write_text("not ours\n", encoding="utf-8")

    run_update(tmp_path, force=True)

    text = foreign.read_text(encoding="utf-8")
    assert text != "not ours\n"
    assert "name: caveman" in text
